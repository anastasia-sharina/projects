"""
A/B recommendation service (service_ab.py)

Purpose:
- Assign users to control / test group (A/B) deterministically and return recommendations
  using two separate models (control / test).

Security:
- Database access is performed via the shared DB connector module
  (0_recsys_movies_ru_common/db_connect.py). Credentials are managed centrally.
"""
import sys
import os
from datetime import datetime
import hashlib
from typing import List, Tuple

import pandas as pd
from catboost import CatBoostClassifier
from fastapi import FastAPI
from loguru import logger
from pydantic import BaseModel

# Import shared get_engine from the common folder (0_recsys_movies_ru_common)
# This centralizes credentials so they are not hardcoded in this service.
sys.path.append('../common')
from db_connect import get_engine

# --- Pydantic response models ---
class PostGet(BaseModel):
    id: int
    text: str
    topic: str

    class Config:
        orm_mode = True

class Response(BaseModel):
    exp_group: str
    recommendations: List[PostGet]

app = FastAPI(title="Recsys A/B Service", version="1.0")

# -------------------- Database utilities and data loading --------------------
def batch_load_sql(query: str, chunksize: int = 200000) -> pd.DataFrame:
    """
    Load data from the DB in chunks using get_engine().
    Returns the concatenated DataFrame.
    """
    engine = get_engine()
    conn = engine.connect().execution_options(stream_results=True)
    chunks = []
    for chunk_dataframe in pd.read_sql(query, conn, chunksize=chunksize):
        chunks.append(chunk_dataframe)
        logger.info("Received chunk of size: %s", len(chunk_dataframe))
    conn.close()
    if not chunks:
        return pd.DataFrame()
    return pd.concat(chunks, ignore_index=True)

def load_raw_features() -> dict:
    """
    Load base tables:
    - liked_posts: (post_id, user_id) pairs with action 'like'
    - posts_features_test: post features for test table (anastasia_sharina_77)
    - posts_features_control: post features for control table (anastasia_sharina_7)
    - user_features: user features
    """
    logger.info("Loading liked posts")
    liked_posts_query = """
        SELECT distinct post_id, user_id
        FROM public.feed_data
        WHERE action='like'
    """
    liked_posts = batch_load_sql(liked_posts_query)

    # Use the shared engine to avoid hardcoding connection strings here.
    engine = get_engine()

    logger.info("Loading post features (TEST, table anastasia_sharina_77)")
    posts_features_test = pd.read_sql(
        "SELECT * FROM public.anastasia_sharina_77",
        con=engine
    )

    logger.info("Loading post features (CONTROL, table anastasia_sharina_7)")
    posts_features_control = pd.read_sql(
        "SELECT * FROM public.anastasia_sharina_7",
        con=engine
    )

    logger.info("Loading user features")
    user_features = pd.read_sql(
        "SELECT * FROM public.user_data",
        con=engine
    )

    return {
        "liked_posts": liked_posts,
        "user_features": user_features,
        "posts_features_test": posts_features_test,
        "posts_features_control": posts_features_control,
    }

# -------------------- Model loading --------------------
def get_model_path(model_version: str) -> str:
    """
    Return model path depending on environment.
    """
    logger.debug("get_model_path called, IS_LMS=%s", os.environ.get("IS_LMS"))
    if os.environ.get("IS_LMS") == "1":
        return f"/workdir/user_input/model_{model_version}"
    else:
        if model_version == "control":
            return "/Users/anastasiasharina/Documents/ML_Engineer_karpov/Lessons/Module_2_Machine_Learning/final_project/model"
        elif model_version == "test":
            return "/Users/anastasiasharina/Documents/ML_Engineer_karpov/Lessons/Module_3_Deep_Learning/final_project/model.cbm"
        else:
            raise ValueError("Unknown model_version")

def load_models(model_version: str) -> CatBoostClassifier:
    model_path = get_model_path(model_version)
    model = CatBoostClassifier()
    model.load_model(model_path)
    # Log only basename to avoid revealing full local paths in logs
    logger.info("Model version '%s' loaded (file: %s)", model_version, os.path.basename(model_path))
    return model

# -------------------- Initialization (load data and models on startup) --------------------
logger.info("Initializing service: loading data and models...")
data = load_raw_features()
model_control = load_models("control")
model_test = load_models("test")
logger.info("Initialization completed")

# -------------------- A/B assignment --------------------
# Salt for deterministic assignment; can be set via AB_SALT env var
SALT = os.environ.get("AB_SALT", "my_salt")

def get_user_group(id: int) -> str:
    """
    Deterministically assign user_id to a group using md5(id + salt).
    Returns 'control' or 'test'.
    """
    value_str = f"{id}{SALT}"
    value_num = int(hashlib.md5(value_str.encode()).hexdigest(), 16)
    percent = value_num % 100
    return "control" if percent < 50 else "test"

# -------------------- Feature preparation and prediction --------------------
def calculate_features(id: int, time: datetime, group: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Prepare features: fetch user features, broadcast them to all posts,
    add time features and return (user_features, user_posts_features, content).
    """
    logger.info("Reading features for user_id=%s", id)

    user_features = data["user_features"].loc[data["user_features"].user_id == id]
    if user_features.empty:
        logger.warning("User %s not found in user_features", id)
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    user_features = user_features.drop("user_id", axis=1)

    logger.info("Selecting post features depending on group: %s", group)
    if group == "control":
        posts_features = data["posts_features_control"].copy()
        drop_cols = [c for c in ["index", "text"] if c in posts_features.columns]
        if drop_cols:
            posts_features = posts_features.drop(drop_cols, axis=1)
        content = data["posts_features_control"][["post_id", "text", "topic"]]
    else:
        posts_features = data["posts_features_test"].copy()
        if "index" in posts_features.columns:
            posts_features = posts_features.drop(["index"], axis=1)
        content = data["posts_features_test"][["post_id", "topic"]]

    # Broadcast user features to all rows in the posts table
    add_user_features = dict(zip(user_features.columns, user_features.values[0]))
    user_posts_features = posts_features.assign(**add_user_features)
    user_posts_features = user_posts_features.set_index("post_id")

    # Add time features
    user_posts_features["hour"] = time.hour
    user_posts_features["month"] = time.month

    return user_features, user_posts_features, content

def get_recommended_feed(id: int, time: datetime, limit: int) -> Response:
    """
    Main recommendation logic:
    1) Determine user's group
    2) Prepare features
    3) Predict probability of like
    4) Remove already liked posts
    5) Return top-N recommendations and the group (exp_group)
    """
    user_group = get_user_group(id=id)
    logger.info("User %s assigned to group: %s", id, user_group)

    if user_group == "control":
        model = model_control
        features_order = [
            'topic', 'TotalTfIdf', 'MaxTfIdf', 'MeanTfIdf', 'TextCluster',
            'DistanceTo1thCluster', 'DistanceTo2thCluster', 'DistanceTo3thCluster',
            'DistanceTo4thCluster', 'DistanceTo5thCluster', 'DistanceTo6thCluster',
            'DistanceTo7thCluster', 'DistanceTo8thCluster', 'DistanceTo9thCluster',
            'DistanceTo10thCluster', 'DistanceTo11thCluster', 'DistanceTo12thCluster',
            'DistanceTo13thCluster', 'DistanceTo14thCluster', 'DistanceTo15thCluster',
            'gender', 'age', 'country', 'city', 'exp_group', 'os', 'source', 'hour', 'month'
        ]
        cat_features_list = [
            'topic', 'TextCluster', 'gender', 'country',
            'city', 'exp_group', 'hour', 'month',
            'os', 'source'
        ]
    elif user_group == "test":
        model = model_test
        features_order = [
            "hour", "month", "gender", "age", "country", "city", "exp_group", "os", "source",
            "topic", "TextCluster",
            "DistanceToCluster_0", "DistanceToCluster_1", "DistanceToCluster_2", "DistanceToCluster_3",
            "DistanceToCluster_4", "DistanceToCluster_5", "DistanceToCluster_6", "DistanceToCluster_7",
            "DistanceToCluster_8", "DistanceToCluster_9", "DistanceToCluster_10", "DistanceToCluster_11",
            "DistanceToCluster_12", "DistanceToCluster_13", "DistanceToCluster_14"
        ]
        cat_features_list = [
            'topic', 'TextCluster', 'gender', 'country',
            'city', 'exp_group', 'hour', 'month',
            'os', 'source'
        ]
    else:
        raise ValueError("unknown group")

    user_features, user_posts_features, content = calculate_features(id=id, time=time, group=user_group)
    if user_posts_features.empty:
        logger.error("Failed to prepare features for user %s", id)
        return Response(exp_group=user_group, recommendations=[])

    # Check that all required columns for the chosen model are present
    missing = [c for c in features_order if c not in user_posts_features.columns]
    if missing:
        logger.error("Missing columns for group %s: %s", user_group, missing)
        raise KeyError(f"Missing columns for group {user_group}: {missing}")
    user_posts_features = user_posts_features[features_order]

    # Convert categorical features to strings (as during training) and fill missing values
    for col in cat_features_list:
        if col in user_posts_features.columns:
            user_posts_features[col] = user_posts_features[col].astype(str).fillna("nan")

    logger.info("Performing probability prediction")
    predicts = model.predict_proba(user_posts_features)[:, 1]
    user_posts_features["predicts"] = predicts

    logger.info("Filtering already liked posts")
    liked_posts = data["liked_posts"]
    liked_post_ids = liked_posts[liked_posts.user_id == id].post_id.values
    filtered_ = user_posts_features[~user_posts_features.index.isin(liked_post_ids)]

    recommended_posts = filtered_.sort_values("predicts", ascending=False).head(limit).index

    # Prepare recommendations list (text is available only in control table)
    recommendations = []
    for i in recommended_posts:
        row = content[content.post_id == i]
        topic_val = row.topic.values[0] if "topic" in row.columns and not row.topic.isnull().all() else ""
        text_val = row.text.values[0] if "text" in row.columns and not row.text.isnull().all() else ""
        recommendations.append(PostGet(id=int(i), text=text_val, topic=topic_val))

    logger.info("Recommendations prepared for user_id=%s, group=%s", id, user_group)
    return Response(exp_group=user_group, recommendations=recommendations)

# --- API endpoint ---
@app.get("/post/recommendations/", response_model=Response)
def recommended_posts(id: int, time: datetime, limit: int = 10) -> Response:
    return get_recommended_feed(id, time, limit)
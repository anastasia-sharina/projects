# Service for receiving post recommendations

import sys
sys.path.append('../common')

import os
import pandas as pd
from typing import List
from catboost import CatBoostClassifier
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from db_connect import get_engine

# Define the data model for the post
class PostGet(BaseModel):
    id: int
    text: str
    topic: str

    # Enable ORM support for database integration
    class Config:
        orm_mode = True

app = FastAPI()

def batch_load_sql(query: str):
    # Load data from the SQL query in large chunks to save memory
    engine = get_engine()
    conn = engine.connect().execution_options(stream_results=True)
    chunks = []
    for chunk_dataframe in pd.read_sql(query, conn, chunksize=200000):
        chunks.append(chunk_dataframe)
        logger.info(f"We have chunk: {len(chunk_dataframe)}")
    conn.close()
    # Combine all chunks into one dataframe
    return pd.concat(chunks, ignore_index=True)

def get_model_path(path: str) -> str:
    # Determine the path to the CatBoost model depending on the environment
    if os.environ.get("IS_LMS") == "1":
        MODEL_PATH = '/workdir/user_input/model'
    else:
        MODEL_PATH = path
    return MODEL_PATH

def load_features():
    # Loading features for the model
    logger.info("Loading liked posts")
    liked_posts_query = """
        SELECT distinct post_id, user_id
        FROM public.feed_data
        WHERE action = 'like'
    """
    liked_posts = batch_load_sql(liked_posts_query)

    engine = get_engine()

    logger.info("Loading post features")
    posts_features = pd.read_sql(
        """SELECT * FROM public.anastasia_sharina_77""",
        con=engine
    )

    logger.info("Loading user features")
    user_features = pd.read_sql(
        """SELECT * FROM public.user_data""",
        con=engine
    )

    return [liked_posts, posts_features, user_features]

def load_models():
    # Load the trained CatBoost model from the file
    model_path = get_model_path("/Users/anastasiasharina/Documents/ML_Engineer_karpov/Lessons/Module_3_Deep_Learning/final_project/model.cbm")
    loaded_model = CatBoostClassifier()
    loaded_model.load_model(model_path)
    return loaded_model

# When the service starts, immediately load the model and features
logger.info("Loading model")
model = load_models()
logger.info("Loading features")
features = load_features()
logger.info("Service initialized and running")

# List of categorical features, as during training
object_cols = [
    'topic', 'TextCluster', 'gender', 'country',
    'city', 'exp_group', 'hour', 'month', 
    'os', 'source'
]

# Final order of features based on training X
features_order = [ 
    "hour", 
    "month", 
    "gender" 
    "age", 
    "country", 
    "city", 
    "exp_group", 
    "os", 
    "source", 
    "topic", 
    "TextCluster" 
    "DistanceToCluster_0", 
    "DistanceToCluster_1", 
    "DistanceToCluster_2", 
    "DistanceToCluster_3", 
    "DistanceToCluster_4", 
    "DistanceToCluster_5", 
    "DistanceToCluster_6", 
    "DistanceToCluster_7", 
    "DistanceToCluster_8", 
    "DistanceToCluster_9", 
    "DistanceToCluster_10", 
    "DistanceToCluster_11",
    "DistanceToCluster_12",
    "DistanceToCluster_13",
    "DistanceToCluster_14"
]

def get_recommended_feed(id: int, time: datetime, limit: int):
    # Generate recommendations for the user
    logger.info(f"user_id: {id}")

    # 1. User features
    user_features = features[2].loc[features[2].user_id == id].drop('user_id', axis=1)
    if user_features.empty:
        logger.warning(f"User {id} not found in user_features!")
        return []

    # 2. Post features
    posts_features = features[1].copy()
    content = features[1][['post_id', 'topic']]

    # 3. Add user features to each post (broadcast)
    user_dict = dict(zip(user_features.columns, user_features.values[0]))
    user_post_features = posts_features.assign(**user_dict)
    user_post_features = user_post_features.set_index('post_id')

    # 4. Add time-based features
    user_post_features['hour'] = time.hour
    user_post_features['month'] = time.month

    # 5. Convert categorical features to a string
    for col in object_cols:
        if col in user_post_features.columns:
            user_post_features[col] = user_post_features[col].astype(str)

    # Form X in the desired order
    X = user_post_features[features_order]

    # 6. Predict the like probability for all posts
    predicts = model.predict_proba(X)[:, 1]
    user_post_features["predicts"] = predicts

    # 7. Remove already liked posts
    liked_posts = features[0]
    liked_post_ids = liked_posts[liked_posts.user_id == id].post_id.values
    filtered_ = user_post_features[~user_post_features.index.isin(liked_post_ids)]

    # 8. Rank by probability and return the top 5
    recommended_posts = filtered_.sort_values('predicts', ascending=False).head(limit).index 

    return [ 
        PostGet( 
            id=int(i), 
            topic=content[content.post_id == i].topic.values[0] 
        ) 
        for i in recommended_posts 
    ]

# Endpoint for receiving recommended posts to the user
@app.get("/post/recommendations/", response_model=List[PostGet])
def recommended_posts(id: int, time: datetime, limit: int = 10) -> List[PostGet]: 
return get_recommended_feed(id, time, limit)
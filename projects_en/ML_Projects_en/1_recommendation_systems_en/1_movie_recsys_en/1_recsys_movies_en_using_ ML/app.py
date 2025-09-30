# Service for receiving movie post recommendations

import sys
sys.path.append('../common')

import os
import pandas as pd
from typing import List
from catboost import CatBoostClassifier
from fastapi import FastAPI
from datetime import datetime
from loguru import logger

from db_connect import get_engine

from pydantic import BaseModel

# Define a data model for a post
class PostGet(BaseModel):
    id: int
    text: str
    topic: str

    # Enable ORM mode for integration with the database
    class Config:
        orm_mode = True

app = FastAPI()

def batch_load_sql(query: str):
    # Load data from an SQL query in large chunks to save memory
    engine = get_engine()
    conn = engine.connect().execution_options(stream_results=True)
    chunks = []
    for chunk_dataframe in pd.read_sql(query, conn, chunksize=200000):
        chunks.append(chunk_dataframe)
        logger.info(f"Got chunk: {len(chunk_dataframe)}")
    conn.close()
    # Combine all chunks into a single DataFrame
    return pd.concat(chunks, ignore_index=True)

def get_model_path(path: str) -> str:
    # Determine the path to the CatBoost model depending on the environment
    if os.environ.get("IS_LMS") == "1":
        MODEL_PATH = '/workdir/user_input/model'
    else:
        MODEL_PATH = path
    return MODEL_PATH

def load_features():
    # Load features for the model
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
        """SELECT * FROM public.posts_info_features""",
        con=engine
    )

    logger.info("Loading user features")
    user_features = pd.read_sql(
        """SELECT * FROM public.user_data""",
        con=engine
    )    

    return [liked_posts, posts_features, user_features]

def load_models():
    # Load a trained CatBoost model from file
    model_path = get_model_path("/Users/anastasiasharina/Documents/ML_Engineer_karpov/Lessons/Module_2_Machine_Learning/final_project/model")
    loaded_model = CatBoostClassifier()
    loaded_model.load_model(model_path)
    return loaded_model

# On service startup, immediately load the model and features
logger.info("Loading model")
model = load_models()
logger.info("Loading features")
features = load_features()
logger.info("Service initialized and running")

def get_recommended_feed(id: int, time: datetime, limit: int):
    # Generate recommendations for the user
    logger.info(f"user_id: {id}")
    logger.info("Reading features")
    user_features = features[2].loc[features[2].user_id == id]
    user_features = user_features.drop('user_id', axis=1)

    logger.info("Dropping columns")
    posts_features = features[1].drop(['index', 'text'], axis=1)
    content = features[1][['post_id', 'text', 'topic']]

    logger.info("Merging everything")
    add_user_features = dict(zip(user_features.columns, user_features.values[0]))
    logger.info("Assigning everything")
    user_post_features = posts_features.assign(**add_user_features)
    user_post_features = user_post_features.set_index('post_id')

    logger.info("Adding time information")
    user_post_features['hour'] = time.hour
    user_post_features['month'] = time.month

    logger.info("Predicting")
    predicts = model.predict_proba(user_post_features)[:, 1]
    user_post_features["predicts"] = predicts

    logger.info("Removing already liked posts")
    liked_posts = features[0]
    liked_posts = liked_posts[liked_posts.user_id == id].post_id.values
    filtered_ = user_post_features[~user_post_features.index.isin(liked_posts)]

    # Select the top-N posts by like probability
    recommended_posts = filtered_.sort_values('predicts')[-limit:].index

    return [
        PostGet(**{
            "id": i,
            "text": content[content.post_id == i].text.values[0],
            "topic": content[content.post_id == i].topic.values[0]
        }) for i in recommended_posts
    ]

# Endpoint for getting recommended posts for a user
@app.get("/post/recommendations/", response_model=List[PostGet])
def recommended_posts(id: int, time: datetime, limit: int = 10) -> List[PostGet]:
    return get_recommended_feed(id, time, limit)

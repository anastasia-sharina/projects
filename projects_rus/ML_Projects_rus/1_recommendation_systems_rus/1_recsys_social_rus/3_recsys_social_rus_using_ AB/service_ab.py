"""
A/B сервис рекомендаций (service_ab.py)

Назначение:
Распределение пользователей на контрольную / тестовую группу (A/B) и выдача рекомендаций с использованием двух моделей (control / test).

Безопасность:
Доступ к базе данных осуществляется через общий модуль подключения (0_recsys_movies_ru_common/db_connect.py).
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

# Подключаем общий модуль с get_engine из папки common (0_recsys_movies_ru_common)
# Это маскирует credentials — все параметры подключения берутся из переменных окружения в одном месте.
sys.path.append('../common')
from db_connect import get_engine

# --- Pydantic-модели ответа ---
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

# -------------------- Работа с базой и загрузка данных --------------------
def batch_load_sql(query: str, chunksize: int = 200000) -> pd.DataFrame:
    """
    Загружает данные из БД чанками через get_engine().
    Возвращает объединённый DataFrame.
    """
    engine = get_engine()
    conn = engine.connect().execution_options(stream_results=True)
    chunks = []
    for chunk_dataframe in pd.read_sql(query, conn, chunksize=chunksize):
        chunks.append(chunk_dataframe)
        logger.info(f"Получен чанк размера: {len(chunk_dataframe)}")
    conn.close()
    if not chunks:
        return pd.DataFrame()
    return pd.concat(chunks, ignore_index=True)

def load_raw_features() -> dict:
    """
    Загружает основные таблицы:
    - liked_posts: пары (post_id, user_id) с действием 'like'
    - posts_features_test: признаки постов для тестовой таблицы (anastasia_sharina_77)
    - posts_features_control: признаки постов для контрольной таблицы (anastasia_sharina_7)
    - user_features: признаки пользователей
    """
    logger.info("Загружаем залайканные посты")
    liked_posts_query = """
        SELECT distinct post_id, user_id
        FROM public.feed_data
        WHERE action='like'
    """
    liked_posts = batch_load_sql(liked_posts_query)

    # Используем единый engine, чтобы не хардкодить connection string в нескольких местах.
    engine = get_engine()

    logger.info("Загружаем признаки постов (TEST, таблица anastasia_sharina_77)")
    posts_features_test = pd.read_sql(
        "SELECT * FROM public.anastasia_sharina_77",
        con=engine
    )

    logger.info("Загружаем признаки постов (CONTROL, таблица anastasia_sharina_7)")
    posts_features_control = pd.read_sql(
        "SELECT * FROM public.anastasia_sharina_7",
        con=engine
    )

    logger.info("Загружаем признаки пользователей")
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

# -------------------- Загрузка моделей --------------------
def get_model_path(model_version: str) -> str:
    """
    Возвращает путь к модели в зависимости от окружения.
    """
    logger.debug("get_model_path вызван, IS_LMS=%s", os.environ.get("IS_LMS"))
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
    # Показываем только имя файла модели, чтобы не раскрывать полный путь в логах
    logger.info("Модель версии '%s' загружена (файл: %s)", model_version, os.path.basename(model_path))
    return model

# -------------------- Инициализация (загрузка данных и моделей при старте сервиса) --------------------
logger.info("Инициализация сервиса: загрузка данных и моделей...")
data = load_raw_features()
model_control = load_models("control")
model_test = load_models("test")
logger.info("Инициализация завершена")

# -------------------- A/B распределение --------------------
# Соль для детерминированного распределения; можно задать через AB_SALT в окружении
SALT = os.environ.get("AB_SALT", "my_salt")

def get_user_group(id: int) -> str:
    """
    Детерминированно распределяет user_id по группам по md5(id + salt).
    Возвращает 'control' или 'test'.
    """
    value_str = f"{id}{SALT}"
    value_num = int(hashlib.md5(value_str.encode()).hexdigest(), 16)
    percent = value_num % 100
    return "control" if percent < 50 else "test"

# -------------------- Подготовка признаков и предсказание --------------------
def calculate_features(id: int, time: datetime, group: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Готовит признаки: достаёт признаки пользователя, присваивает их всем постам,
    добавляет временные признаки и возвращает (user_features, user_posts_features, content).
    """
    logger.info("Чтение признаков для user_id=%s", id)

    user_features = data["user_features"].loc[data["user_features"].user_id == id]
    if user_features.empty:
        logger.warning("Пользователь %s не найден в user_features", id)
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    user_features = user_features.drop("user_id", axis=1)

    logger.info("Выбираем признаки постов в зависимости от группы: %s", group)
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

    # Broadcast признаков пользователя на все строки таблицы постов
    add_user_features = dict(zip(user_features.columns, user_features.values[0]))
    user_posts_features = posts_features.assign(**add_user_features)
    user_posts_features = user_posts_features.set_index("post_id")

    # Добавляем временные признаки
    user_posts_features["hour"] = time.hour
    user_posts_features["month"] = time.month

    return user_features, user_posts_features, content

def get_recommended_feed(id: int, time: datetime, limit: int) -> Response:
    """
    Основная логика выдачи рекомендаций:
    1) Определяем группу пользователя
    2) Подготавливаем признаки
    3) Делаем предсказания вероятности лайка
    4) Убираем уже залайканные посты
    5) Возвращаем топ-N рекомендаций и группу (exp_group)
    """
    user_group = get_user_group(id=id)
    logger.info("User %s отнесён к группе: %s", id, user_group)

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
        logger.error("Не удалось подготовить признаки для пользователя %s", id)
        return Response(exp_group=user_group, recommendations=[])

    # Проверяем наличие всех необходимых колонок для выбранной модели
    missing = [c for c in features_order if c not in user_posts_features.columns]
    if missing:
        logger.error("Отсутствуют колонки для группы %s: %s", user_group, missing)
        raise KeyError(f"Отсутствуют колонки для группы {user_group}: {missing}")
    user_posts_features = user_posts_features[features_order]

    # Приводим категориальные признаки к строкам (как при обучении) и заполняем пропуски
    for col in cat_features_list:
        if col in user_posts_features.columns:
            user_posts_features[col] = user_posts_features[col].astype(str).fillna("nan")

    logger.info("Выполняем предсказание вероятностей")
    predicts = model.predict_proba(user_posts_features)[:, 1]
    user_posts_features["predicts"] = predicts

    logger.info("Фильтруем уже залайканные посты")
    liked_posts = data["liked_posts"]
    liked_post_ids = liked_posts[liked_posts.user_id == id].post_id.values
    filtered_ = user_posts_features[~user_posts_features.index.isin(liked_post_ids)]

    recommended_posts = filtered_.sort_values("predicts", ascending=False).head(limit).index

    # Формируем список рекомендаций (text есть только в контрольной таблице)
    recommendations = []
    for i in recommended_posts:
        row = content[content.post_id == i]
        topic_val = row.topic.values[0] if "topic" in row.columns and not row.topic.isnull().all() else ""
        text_val = row.text.values[0] if "text" in row.columns and not row.text.isnull().all() else ""
        recommendations.append(PostGet(id=int(i), text=text_val, topic=topic_val))

    logger.info("Рекомендации подготовлены для user_id=%s, группа=%s", id, user_group)
    return Response(exp_group=user_group, recommendations=recommendations)

# --- Эндпоинт API ---
@app.get("/post/recommendations/", response_model=Response)
def recommended_posts(id: int, time: datetime, limit: int = 10) -> Response:
    return get_recommended_feed(id, time, limit)
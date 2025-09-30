# Project Description

This project implements three microservices for a recommendation system: one for classic Machine Learning (ML), one for Deep Learning (DL), and one for AB testing of ML and DL models. Each service can be run independently via Docker.

The project includes the steps of loading and analyzing data from the database, generating features, training and evaluating the quality of models, saving the trained model, and developing API services for online recommendations. Each service provides personalized recommendations for users based on their features and interaction history.

## Results

- A scalable architecture with three independent services (ML, DL, AB) has been achieved.
- Each service implements best practices for working with models, APIs, and secure database connections.
- All services are tested and ready for deployment and use.
- The project demonstrates skills in ML, DL, APIs, Docker, and working with industrial code.

## Tech Stack

- **Python 3.8+** — primary development language.
- **Pandas, NumPy** — tabular data processing and analysis.
- **scikit-learn** — classic ML algorithms, feature processing, clustering, and metrics.
- **CatBoost** — the main ML model for ranking and recommendations.
- **NLTK** — text lemmatization for the ML pipeline.
- **PyTorch** — deep learning, embedding construction, and integration with HuggingFace Transformers.
- **HuggingFace Transformers** — embedding generation using BERT, RoBERTa, and DistilBERT.
- **tqdm** — progress bar for inference and training.
- **SQLAlchemy** — connecting to and working with a PostgreSQL database.
- **PostgreSQL** — storing source, intermediate, and result data.
- **FastAPI** — implementing API services for recommendations.
- **Pydantic** — describing data schemas and serialization for APIs.
- **Docker** — containerization of services for easy deployment and scaling.
- **Seaborn, Matplotlib** — visualization of feature and metric analysis.
- **category_encoders** — OneHotEncoder, TargetEncoder for processing categorical features.
- **Jupyter Notebook** — experimental analysis, training pipelines.
- **loguru** — logging of service operations.

## Service Description

- **ML Service:** Classic ML models for recommendations, fast inference.
- **DL service:** Deep learning on transformers, text processing, embedding clustering.
- **AB service:** Conducting AB testing of ML and DL models, analyzing results, and performing statistics.

## Data

- Tabular data on user interactions with posts and their text content are used.
- Data is stored in PostgreSQL, the structure is described in the corresponding .ipynb files.
- Mock data from test scripts can be used for testing.

## Project Quality Metrics

- **ROC-AUC (Receiver Operating Characteristic - Area Under Curve):**
    - The primary metric for assessing the quality of recommendation ranking.
    - Used both during the training of ML models (CatBoost, DecisionTree) and DL models.
    - Allows for objective comparison of different algorithms and approaches.

- **Hitrate:**
    - The final metric for assessing the quality of recommendations in LMS and during integration testing.
    - Shows the proportion of cases where a recommended post was actually viewed or liked by the user.

- **Feature Importance:**
    - Analyzed for CatBoost models and other ML algorithms.
    - Visualizing feature importance helps understand the contribution of text, cluster, time, and user features.

- **Precision, Recall, F1-score:**
    - Used for additional model evaluation during binary classification (like/dislike).
    - Allows you to evaluate the balance between recall and precision of recommendations.

- **AB Testing:**
    - Used to compare the performance of different models or algorithms (ML vs. DL).
    - Evaluates statistically significant differences in metrics on real users.

- **Error and Deviation Logging:**
    - Logging systems allow you to track abnormal situations, anomalies, and service performance in production.

## Testing

- The project includes unit tests for each service.
- You can use FastAPI TestClient and curl to test the API (see below).

## API Usage Example

```python
import requests
r = requests.get("http://localhost:8000/post/recommendations/", params={"id": 1000, "time": "2021-12-20T00:00:00", "limit": 5})
print(r.json())
```

## Installing Dependencies

```bash
pip install -r common/requirements.txt
```

## Docker Run

### ML Service (ml/app.py)
```bash
docker build -t ml-dl-ab --build-arg PROJECT=ml --build-arg SERVICE_FILE=app.py .
docker run --env-file common/.env -p 8000:8000 ml-dl-ab
```

### Deep Learning service (dl/service.py)
```bash
docker build -t ml-dl-ab --build-arg PROJECT=dl --build-arg SERVICE_FILE=service.py .
docker run --env-file common/.env -p 8001:8000 ml-dl-ab
```

### AB testing service (ab/service3.py)
```bash
docker build -t ml-dl-ab --build-arg PROJECT=ab --build-arg SERVICE_FILE=service3.py .
docker run --env-file common/.env -p 8002:8000 ml-dl-ab
```

## Contacts

Author: Anastasia Sharina
GitHub: [anastasia-sharina](https://github.com/anastasia-sharina)
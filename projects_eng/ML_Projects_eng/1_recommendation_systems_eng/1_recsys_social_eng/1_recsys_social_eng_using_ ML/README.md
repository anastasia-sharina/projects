# ML Recommendation System Service

## Description

The ML service implements a classical recommendation system for social posts.  
It is based on a CatBoost model trained on user and post features, including text embeddings, categorical and temporal features, as well as clustering-based features.  
The service provides an API for retrieving personalized recommendations via FastAPI.

## Pipeline Stages

1. **Data loading and preprocessing**  
   - Import and clean data from PostgreSQL via the shared module `common/db_connect.py`.  
   - Analyze data structure, handle missing values, and generate new features.  

2. **Feature engineering**  
   - TF-IDF transformation of texts, lemmatization with NLTK.  
   - Dimensionality reduction (PCA), clustering (KMeans), adding cluster distances.  
   - Generating temporal features (`hour`, `month`), handling categorical features (OneHot, TargetEncoder).  

3. **Model training**  
   - Baseline DecisionTree for comparison.  
   - Main model: CatBoost with parameter tuning, trained on categorical and numerical features.  

4. **Model evaluation**  
   - Primary metric: ROC-AUC (train/test).  
   - Visualization of feature importance.  
   - Example performance:  
     - CatBoost ROC-AUC (train): ~0.77  
     - CatBoost ROC-AUC (test): ~0.76  

5. **Model saving**  
   - The model is saved in `.cbm` format for later use in the service.  

6. **API service**  
   - Implemented with FastAPI for online recommendations.  
   - Endpoint `/post/recommendations/` returns top-N posts for a given user based on the trained model.  

## Results
The service provides an API for retrieving personalized recommendations via FastAPI resulting in Hitrate@5 = 55%.

## Full Tech Stack

- **Python 3.8+**  
- **CatBoost**  
- **scikit-learn**  
- **NLTK**  
- **Pandas, NumPy**  
- **FastAPI**  
- **SQLAlchemy**  
- **PostgreSQL**  
- **Docker**  
- **Seaborn, Matplotlib (feature analysis)**  

## Evaluation Metrics

- **ROC-AUC** — main metric for ranking quality.  
- **Hitrate** — used for final evaluation in LMS.  
- **Feature Importance** — analysis of model feature contributions.  

## How to Run

### Locally

1. Install dependencies:
    ```bash
    pip install -r ../common/requirements.txt
    ```

2. Run the service:
    ```bash
    python service_ml.py
    ```

### Via Docker

```bash
docker build -t ml-dl-ab --build-arg PROJECT=ml --build-arg SERVICE_FILE=service_ml.py .
docker run --env-file ../common/.env -p 8000:8000 ml-dl-ab

## API Request Example

```python
import requests
r = requests.get(
    "http://localhost:8000/post/recommendations/", 
    params={"id": 1000, "time": "2021-12-20T00:00:00", "limit": 5}
)
print(r.json())
```

## Testing

- Unit tests for the service are located in `test.py`.
- To test the API, use FastAPI TestClient or curl.

## Contacts

Author: Anastasia Sharina
GitHub: [anastasia-sharina](https://github.com/anastasia-sharina)

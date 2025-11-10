# DL Recommendation System Service

## Description

The DL service implements a recommendation system based on modern transformers (BERT, RoBERTa, DistilBERT) for generating post text embeddings. Clustering of embeddings and calculation of cluster distances are used as additional features for the CatBoost model. The service provides an API for receiving recommendations via FastAPI.

## Pipeline Stages

1. **Data Loading and Analysis**  
   - Import data from PostgreSQL using the shared module `common/db_connect.py`.
   - Text preprocessing, structure analysis, handling of missing values.

2. **Embedding Generation**  
   - Use pretrained models: BERT, RoBERTa, DistilBERT from HuggingFace Transformers.
   - Build dataset and DataLoader (PyTorch DataLoader), automatic padding (DataCollator).

3. **Embedding Clustering**  
   - Dimensionality reduction (PCA).
   - KMeans clustering, adding cluster distances and labels to posts.

4. **Feature Storage**  
   - Post features (embeddings, clusters, distances) are saved in PostgreSQL for further use in models.

5. **CatBoost Model Training**  
   - Merge embedding features with user features.
   - Train CatBoost on the full feature set.

6. **API Service**  
   - Implement FastAPI for online recommendations.
   - Endpoint `/post/recommendations/` returns top-N posts for a user.

## Full Tech Stack

- **Python 3.8+**
- **PyTorch**
- **Transformers (HuggingFace)**
- **CatBoost**
- **scikit-learn**
- **Pandas, NumPy**
- **FastAPI**
- **SQLAlchemy**
- **PostgreSQL**
- **Docker**
- **tqdm (inference)**

## Evaluation Metrics

- **ROC-AUC** — main metric for the CatBoost model (train/test).
- **Hitrate** — final metric for LMS.
- **Feature Importance** — analysis of embedding and clustering feature impact.

## How to Run

### Locally

1. Install dependencies:
    ```bash
    pip install -r ../common/requirements.txt
    ```

2. Run the service:
    ```bash
    python service_dl.py
    ```

### Via Docker

```bash
docker build -t ml-dl-ab --build-arg PROJECT=dl --build-arg SERVICE_FILE=service_dl.py .
docker run --env-file ../common/.env -p 8001:8000 ml-dl-ab


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

- Unit tests for the service are in `testing.py`.
- To test the API, use FastAPI TestClient or curl.

## Contacts

Author: Anastasia Sharina
GitHub: [anastasia-sharina](https://github.com/anastasia-sharina)
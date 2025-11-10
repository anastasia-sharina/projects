# A/B Recommendation Service (3_recsys_movies_ru_using_AB)

Overview
- This A/B service deterministically assigns users to control or test groups and returns personalized recommendations using two independent models (control / test).
- The response includes the experiment group (`exp_group`) alongside the recommendations so the result can be used directly in A/B analytics.
- The service demonstrates best practices for portfolio projects: centralized DB connection (credentials masked in a common module), clear Russian/English logs and comments in code, and a well-documented pipeline.

Pipeline / Architecture
1. Data loading
   - Interaction data (feed_data) and post/user feature tables are loaded from PostgreSQL using the shared module `0_recsys_movies_ru_common/db_connect.py`.
   - Large tables are read in chunks (batch load) to save memory.
2. Feature preparation
   - User features are broadcast to the posts table (user->post join by broadcasting).
   - Time features (hour, month) are added.
   - Categorical features are converted to strings and NaNs are filled explicitly.
3. A/B assignment
   - Deterministic assignment using md5(user_id + SALT). SALT is read from environment variable `AB_SALT` (default: `"my_salt"`).
   - Default split: 50% control, 50% test.
4. Inference and ranking
   - Each group uses its own feature ordering and corresponding CatBoost model.
   - The service predicts probability of a "like", filters out already liked posts, ranks by probability and returns top-N.
5. A/B analysis support
   - The service returns `exp_group` together with recommendations to facilitate logging and A/B analysis downstream.

Tech stack
- Python 3.8+
- FastAPI (REST API)
- CatBoost (models)
- Pandas, NumPy
- SQLAlchemy (DB engine created in common module)
- PostgreSQL
- loguru (logging)
- Docker (containerization)

Quality metrics
- ROC-AUC — primary metric for ranking performance.
- Hitrate — used for final evaluation in integration tests / LMS.
- Feature importance — analysis of model feature contributions.

Security
- All DB credentials are centralized in `0_recsys_movies_ru_common/db_connect.py` and read from environment (.env) locally. The service code itself does not contain hardcoded connection strings.
- For local development: copy `0_recsys_movies_ru_common/.env.example` -> `0_recsys_movies_ru_common/.env` and fill values. Do NOT commit `.env`.
- The service does not log the full environment or full connection strings. Only safe indicators are logged (for example, the presence of `IS_LMS` or the basename of a model file).
- For production, store secrets in a secret manager or CI/CD environment variables.

Environment variables used
- IS_LMS — if equal to `"1"`, service will use LMS model path.
- AB_SALT — optional salt for A/B hashing (default: `"my_salt"`).
- DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME — used by the common DB connector (see `0_recsys_movies_ru_common/.env.example`).

Installation
```bash
# Install dependencies (shared requirements in common)
pip install -r ../0_recsys_movies_ru_common/requirements.txt
```

Run locally
1. Prepare local `.env`:
   - Copy `0_recsys_movies_ru_common/.env.example` -> `0_recsys_movies_ru_common/.env` and fill the variables.
2. Start the service:
```bash
# from the project root (folder that contains package 3_recsys_movies_ru_using_AB)
uvicorn 3_recsys_movies_ru_using_AB.service:app --reload --port 8002
```
3. Example request:
```python
import requests

r = requests.get(
    "http://localhost:8002/post/recommendations/",
    params={"id": 1000, "time": "2021-12-20T00:00:00", "limit": 5}
)
print(r.json())
```
Expected response shape:
```json
{
  "exp_group": "control",
  "recommendations": [
    {"id": 123, "text": "Post description...", "topic": "topic1"},
    ...
  ]
}
```

Docker
- Build and run using the shared Dockerfile (see main README). Example:
```bash
# build (example: PROJECT=ab, SERVICE_FILE=service.py)
docker build -t ml-dl-ab --build-arg PROJECT=ab --build-arg SERVICE_FILE=service.py .
# run (pass env from common and map port 8002)
docker run --env-file ../0_recsys_movies_ru_common/.env -p 8002:8000 ml-dl-ab
```

Testing
- Add unit tests for:
  - deterministic user assignment (get_user_group),
  - feature preparation (calculate_features),
  - API endpoint behavior (FastAPI TestClient).
- For integration tests use a real or mocked database (fixtures).

Notes for reviewers / what to highlight in portfolio
- Centralized secret management: `db_connect.py` isolates credentials and connection logic.
- Clear, documented pipeline with explicit separation of steps: data loading → feature preparation → inference → ranking.
- Safe logging (no raw env vars or connection strings printed).
- Easy local run & Docker setup demonstrated via `.env.example` and Docker commands.

Author / Contacts
Author: Anastasia Sharina  
GitHub: https://github.com/anastasia-sharina
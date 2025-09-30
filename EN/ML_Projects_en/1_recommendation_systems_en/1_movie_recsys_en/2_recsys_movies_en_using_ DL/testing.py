# Testing ecommendation API service using FastAPI TestClient.
# This approach allows you to verify the endpoint's functionality without launching an external server,
# which is convenient for unit testing and validating the business logic of the recommendation system.

import service
from fastapi.testclient import TestClient
from datetime import datetime

client = TestClient(service.app)

user_id = 1000
time = datetime(2021, 12, 20)

try:
    r = client.get(
        "/post/recommendations/",
        params={"id": user_id, "time": time, "limit": 5},
    )
except Exception as e:
    raise ValueError(f"Ошибка при выполнении запроса {type(e)} {str(e)}")

print(r.json())
# Run a test to check the operation of the recommendation system using ML

import app
from fastapi.testclient import TestClient
from datetime import datetime

# Initialize a test client for the FastAPI application
client = TestClient(app.app)

# Set user ID and request time parameters
user_id = 1000
time = datetime(2021, 12, 20)

try:
    # Perform a GET request to the post recommendations endpoint
    r = client.get(
        f"/post/recommendations/",
        params={"id": user_id, "time": time, "limit": 5},
    )
except Exception as e:
    # In case of error, output the exception type and message
    raise ValueError(f"Error during request {type(e)} {str(e)}")

# Print received recommendations in JSON format
print(r.json())
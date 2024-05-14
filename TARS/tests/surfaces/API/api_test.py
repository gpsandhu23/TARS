import pytest
from fastapi.testclient import TestClient
from surfaces.API.api import app

client = TestClient(app)

def test_chat_endpoint_returns_200():
    # Prepare the request data
    request_data = {"message": "Hello", "user_name": "TestUser"}

    # Send a POST request to the /chat endpoint
    response = client.post("/chat", json=request_data)

    # Check if the response status code is 200
    assert response.status_code == 200

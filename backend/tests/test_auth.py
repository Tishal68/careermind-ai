import time
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_register_and_login_flow():
    unique_email = f"testuser_{int(time.time())}@careermind.ai"
    test_user = {
        "email": unique_email,
        "full_name": "Test Engineer",
        "password": "SecurePassword123!"
    }
    
    register_response = client.post("/api/v1/auth/register", json=test_user)
    assert register_response.status_code == 201
    reg_data = register_response.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == test_user["email"]
    
    token = reg_data["access_token"]

    # Retrieve current user profile
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["full_name"] == test_user["full_name"]

    # Login user
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": test_user["email"], "password": test_user["password"]}
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

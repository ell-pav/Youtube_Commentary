from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_login():

    response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
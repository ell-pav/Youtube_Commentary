from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def get_token():

    response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    return response.json()[
        "access_token"
    ]


def test_analyze_requires_auth():

    response = client.post(
        "/analyze",
        json={
            "url": "test",
            "sentiment": "positive"
        }
    )

    assert response.status_code == 401


def test_analyze_with_auth():

    token = get_token()

    headers = {
        "Authorization":
        f"Bearer {token}"
    }

    response = client.post(
        "/analyze",
        json={
            "url": "https://youtube.com/watch?v=test",
            "sentiment": "positive"
        },
        headers=headers
    )

    assert response.status_code in [
        200,
        400
    ]
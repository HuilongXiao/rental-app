from fastapi.testclient import TestClient

from app.main import app


def test_health_and_database_startup():
    with TestClient(app) as client:
        assert client.get("/api/health").json() == {
            "status": "ok",
            "service": "rental-app-api",
        }
        assert client.get("/api/health/database").json() == {
            "status": "ok",
            "database": "connected",
        }


def test_seeded_admin_can_login_and_read_current_user():
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "admin123"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["user"]["username"] == "admin"
        assert "rental_session" in response.cookies

        current_user = client.get("/api/auth/me")
        assert current_user.status_code == 200
        assert current_user.json()["username"] == "admin"


def test_invalid_password_is_rejected():
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "wrong-password"},
        )
        assert response.status_code == 401

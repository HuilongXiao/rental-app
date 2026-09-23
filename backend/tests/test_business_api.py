from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app


def logged_in_client() -> TestClient:
    client = TestClient(app)
    response = client.post("/api/auth/login", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    return client


def test_customer_order_lifecycle_and_payment():
    with logged_in_client() as client:
        customer = client.post("/api/customers", json={"name": "链路测试客户", "phone": "13800000000"})
        assert customer.status_code == 200
        customer_id = customer.json()["id"]

        order = client.post(
            "/api/orders",
            json={
                "customer_id": customer_id,
                "start_at": datetime.now().isoformat(),
                "adult_count": 2,
                "child_count": 0,
                "items": [],
            },
        )
        # An order must contain at least one catalog item.
        assert order.status_code == 422

        payment = client.get("/api/orders/not-found/payment")
        assert payment.status_code == 404


def test_protected_business_routes_require_login():
    with TestClient(app) as client:
        assert client.get("/api/customers").status_code == 401
        assert client.get("/api/catalog").status_code == 401
        assert client.get("/api/inventory").status_code == 401

from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app


def test_health_and_database():
    with TestClient(app) as client:
        assert client.get("/api/health").json()["status"] == "ok"
        assert client.get("/api/health/database").json()["database"] == "connected"


def test_login_and_me():
    with TestClient(app) as client:
        response = client.post("/api/auth/login", data={"username": "admin", "password": "admin123"})
        assert response.status_code == 200
        assert response.json()["user"]["username"] == "admin"
        assert "rental_session" in response.cookies

        me = client.get("/api/auth/me")
        assert me.status_code == 200
        assert me.json()["username"] == "admin"


def test_catalog_and_customer_order_flow():
    with TestClient(app) as client:
        login = client.post("/api/auth/login", data={"username": "admin", "password": "admin123"})
        assert login.status_code == 200

        catalog = client.get("/api/catalog")
        assert catalog.status_code == 200
        body = catalog.json()
        assert body["equipment_types"]
        assert body["equipment"]

        customer = client.post(
            "/api/customers",
            json={"name": "真实链路客户", "phone": "13800000001"},
        )
        assert customer.status_code == 200
        customer_id = customer.json()["id"]

        equipment_id = body["equipment"][0]["id"]
        order = client.post(
            "/api/orders",
            json={
                "customer_id": customer_id,
                "start_at": datetime.now().isoformat(),
                "adult_count": 2,
                "child_count": 0,
                "items": [{"equipment_spec_id": equipment_id, "quantity": 1}],
            },
        )
        assert order.status_code == 200
        order_id = order.json()["id"]

        inventory = client.get("/api/inventory")
        assert inventory.status_code == 200
        assert inventory.json()

        payment = client.get(f"/api/orders/{order_id}/payment")
        assert payment.status_code == 200

        adjustment = client.post(
            f"/api/orders/{order_id}/payment/adjustments",
            json={"quantity": 1, "unit_amount": 50, "note": "smoke test adjustment"},
        )
        assert adjustment.status_code == 200

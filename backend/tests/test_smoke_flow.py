from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def login(client: TestClient) -> None:
    response = client.post("/api/auth/login", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 200, response.text
    assert "rental_session" in response.cookies


def test_health_and_database():
    with TestClient(app) as client:
        assert client.get("/api/health").json() == {"status": "ok", "service": "rental-app-api"}
        assert client.get("/api/health/database").json() == {"status": "ok", "database": "connected"}


def test_login_me_and_logout():
    with TestClient(app) as client:
        login(client)
        me = client.get("/api/auth/me")
        assert me.status_code == 200
        assert me.json()["username"] == "admin"

        assert client.post("/api/auth/logout").status_code == 200
        assert client.get("/api/auth/me").status_code == 401


def test_protected_routes_require_login():
    with TestClient(app) as client:
        for path in ("/api/catalog", "/api/customers", "/api/inventory", "/api/orders"):
            assert client.get(path).status_code == 401


def test_catalog_customer_order_inventory_payment_flow():
    with TestClient(app) as client:
        login(client)

        catalog_response = client.get("/api/catalog")
        assert catalog_response.status_code == 200, catalog_response.text
        catalog = catalog_response.json()
        assert catalog["equipment_types"]
        assert catalog["equipment"]
        equipment = catalog["equipment"][0]

        suffix = uuid4().hex[:10]
        customer_response = client.post(
            "/api/customers",
            json={"name": f"真实链路客户-{suffix}", "phone": f"1{suffix}"},
        )
        assert customer_response.status_code == 200, customer_response.text
        customer_id = customer_response.json()["id"]

        start_at = datetime.now(timezone.utc).replace(microsecond=0)
        order_response = client.post(
            "/api/orders",
            json={
                "customer_id": customer_id,
                "start_at": start_at.isoformat(),
                "end_at": (start_at + timedelta(hours=2)).isoformat(),
                "adult_count": 2,
                "child_count": 0,
                "items": [{"equipment_spec_id": equipment["id"], "quantity": 1}],
            },
        )
        assert order_response.status_code == 200, order_response.text
        order = order_response.json()
        order_id = order["id"]
        assert order["items"][0]["unit_price"] == equipment["price"]

        inventory_before = client.get("/api/inventory")
        assert inventory_before.status_code == 200
        item_before = next(item for item in inventory_before.json() if item["equipment_spec_id"] == equipment["id"])

        check_in = client.post(f"/api/orders/{order_id}/check-in")
        assert check_in.status_code == 200, check_in.text

        inventory_after = client.get("/api/inventory")
        item_after = next(item for item in inventory_after.json() if item["equipment_spec_id"] == equipment["id"])
        assert item_after["occupied_quantity"] == item_before["occupied_quantity"] + 1

        payment_before = client.get(f"/api/orders/{order_id}/payment")
        assert payment_before.status_code == 200
        assert payment_before.json()["amount_fen"] == equipment["price"]

        adjustment = client.post(
            f"/api/orders/{order_id}/payment/adjustments",
            json={"quantity": 1, "unit_amount": 50, "note": "smoke test adjustment"},
        )
        assert adjustment.status_code == 200, adjustment.text
        assert adjustment.json()["amount_fen"] == equipment["price"] + 50

        returned = client.post(f"/api/orders/{order_id}/return", json={"reason": "smoke test complete"})
        assert returned.status_code == 200, returned.text
        assert returned.json()["status"] == "returned"

        inventory_final = client.get("/api/inventory")
        item_final = next(item for item in inventory_final.json() if item["equipment_spec_id"] == equipment["id"])
        assert item_final["occupied_quantity"] == item_before["occupied_quantity"]

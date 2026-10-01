from fastapi.testclient import TestClient

from ordermesh.api import app, repository, service
from ordermesh.repository import InMemoryOrderRepository


def client() -> TestClient:
    fresh = InMemoryOrderRepository()
    repository._orders = fresh._orders
    repository._events = fresh._events
    service.repository = repository
    return TestClient(app)


def payload(order_id: str = "ord-1001") -> dict:
    return {
        "id": order_id,
        "customer_id": "cus-42",
        "items": [{"sku": "SKU-1", "quantity": 2, "unit_price": "19.95"}],
    }


def test_health():
    response = client().get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_confirm_and_read_events():
    c = client()
    created = c.post("/orders", json=payload())
    assert created.status_code == 201
    assert created.json()["total"] == "39.90"

    confirmed = c.post("/orders/ord-1001/confirm")
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "CONFIRMED"

    events = c.get("/orders/ord-1001/events").json()
    assert [event["event_type"] for event in events] == [
        "order.created",
        "order.confirmed",
    ]


def test_duplicate_order_is_conflict():
    c = client()
    assert c.post("/orders", json=payload()).status_code == 201
    assert c.post("/orders", json=payload()).status_code == 409


def test_invalid_transition_is_conflict():
    c = client()
    c.post("/orders", json=payload())
    response = c.post("/orders/ord-1001/fulfill")
    assert response.status_code == 409

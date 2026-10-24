from fastapi.testclient import TestClient

from sloforge.api import app

client = TestClient(app)


def payload() -> dict[str, object]:
    return {
        "target": 0.99,
        "fast_short": {"good": 80, "total": 100},
        "fast_long": {"good": 800, "total": 1000},
        "slow_short": {"good": 99, "total": 100},
        "slow_long": {"good": 990, "total": 1000},
    }


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "sloforge"}


def test_evaluation_exposes_alert_evidence():
    response = client.post("/v1/evaluate", json=payload())

    assert response.status_code == 200
    body = response.json()
    assert body["page"] is True
    assert body["reasons"] == ["fast_burn"]
    assert body["windows"]["fast_short"]["burn_rate"] == 20
    assert body["windows"]["fast_long"]["bad"] == 200
    assert body["remaining_error_budget"] == 0


def test_api_rejects_invalid_counts_and_thresholds():
    invalid_counts = payload() | {"fast_short": {"good": 101, "total": 100}}
    invalid_threshold = payload() | {"slow_threshold": 0}

    assert client.post("/v1/evaluate", json=invalid_counts).status_code == 422
    assert client.post("/v1/evaluate", json=invalid_threshold).status_code == 422

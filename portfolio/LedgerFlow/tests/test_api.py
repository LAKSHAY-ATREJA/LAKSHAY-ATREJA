from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from fastapi.testclient import TestClient
import pytest
from ledgerflow import api
from ledgerflow.domain import Ledger, LedgerError


def test_http_transfer_retry_and_conflict():
    api.ledger = Ledger()
    client = TestClient(api.app)
    payload = {"source": "cash", "destination": "merchant", "amount": "12.50"}
    headers = {"Idempotency-Key": "example"}
    first = client.post("/v1/transfers", json=payload, headers=headers)
    retry = client.post("/v1/transfers", json=payload, headers=headers)
    assert first.status_code == 201
    assert retry.json() == first.json()
    assert client.get("/v1/accounts/merchant/balance").json()["balance"] == "12.50"
    assert len(client.get("/v1/audit").json()) == 1
    assert (
        client.post("/v1/transfers", json={**payload, "amount": "13"}, headers=headers).status_code
        == 400
    )
    assert client.post("/v1/transfers", json=payload).status_code == 422


def test_concurrent_retry_posts_once():
    ledger = Ledger()
    with ThreadPoolExecutor(max_workers=8) as pool:
        ids = list(
            pool.map(lambda _: ledger.transfer("a", "b", Decimal("2"), "same").id, range(30))
        )
    assert len(set(ids)) == 1
    assert ledger.balance("b") == Decimal("2")


@pytest.mark.parametrize(
    "amount", [Decimal("NaN"), Decimal("Infinity"), Decimal("0"), Decimal("-1")]
)
def test_invalid_money_rejected(amount):
    with pytest.raises(LedgerError):
        Ledger().transfer("a", "b", amount, "request")

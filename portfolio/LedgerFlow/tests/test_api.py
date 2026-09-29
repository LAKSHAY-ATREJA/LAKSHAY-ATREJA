import os
os.environ["LEDGER_DB"] = "test_api.db"
from app import app

def test_healthz():
    response = app.test_client().get("/healthz")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}

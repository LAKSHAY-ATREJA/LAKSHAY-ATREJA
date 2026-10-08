from decimal import Decimal
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from .domain import Ledger, LedgerError

app = FastAPI(title="LedgerFlow", version="1.0.0")
ledger = Ledger()


class TransferRequest(BaseModel):
    source: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    amount: Decimal = Field(gt=0)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/transfers", status_code=201)
def transfer(body: TransferRequest, idempotency_key: str = Header(alias="Idempotency-Key")):
    try:
        e = ledger.transfer(body.source, body.destination, body.amount, idempotency_key)
        return {"entry_id": e.id, "reference": e.reference, "created_at": e.created_at}
    except LedgerError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.get("/v1/accounts/{account_id}/balance")
def balance(account_id: str):
    return {"account_id": account_id, "balance": str(ledger.balance(account_id))}


@app.get("/v1/audit")
def audit():
    return [
        {
            "id": e.id,
            "reference": e.reference,
            "postings": [{"account_id": p.account_id, "amount": str(p.amount)} for p in e.postings],
        }
        for e in ledger.audit()
    ]

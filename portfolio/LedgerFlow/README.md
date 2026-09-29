# LedgerFlow

LedgerFlow is a production-style double-entry ledger service built as a portfolio backend project. It demonstrates idempotent transaction posting, balanced journal validation, account balances, REST APIs, automated tests, containerisation and CI.

## Engineering highlights

- Double-entry invariant: every transaction must balance to zero.
- Idempotency keys prevent accidental duplicate posting.
- SQLite persistence with explicit transactional writes.
- Flask REST API with validation and predictable JSON errors.
- Pytest coverage for core accounting invariants and API health.
- Docker image with a health check.
- GitHub Actions CI on every push and pull request.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The API starts on port 8000.

## API

`POST /accounts` creates an account.

```json
{"name":"Cash","type":"asset"}
```

`POST /transactions` posts a balanced journal.

```json
{
  "idempotency_key":"invoice-1001",
  "description":"Customer payment",
  "entries":[
    {"account_id":1,"amount_cents":25000},
    {"account_id":2,"amount_cents":-25000}
  ]
}
```

`GET /accounts/<id>/balance` returns the current balance.

`GET /healthz` is the liveness endpoint.

## Design

Amounts are stored as integer cents to avoid floating-point errors. A transaction and all of its entries are inserted within one database transaction. The service rejects journals with fewer than two entries or a non-zero sum. The idempotency key is unique at the database layer.

## Run tests

```bash
pytest -q
```

## Docker

```bash
docker build -t ledgerflow .
docker run --rm -p 8000:8000 ledgerflow
```

Built by Lakshay Atreja as a software-engineering portfolio project.

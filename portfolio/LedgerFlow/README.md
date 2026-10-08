# LedgerFlow

A small Python/FastAPI service that demonstrates double-entry accounting, safe request retries and an inspectable journal. A transfer debits one account and credits another by the same amount; repeating the same request with the same idempotency key returns the original entry.

**Start here:** run the automated HTTP demo below, then open the interactive API at `/docs`. No accounts, API keys or paid services are needed.

## Run in five minutes

Requires Python 3.11 or newer. From this project directory:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python demo.py
```

On Windows, activate with `.venv\Scripts\activate` instead. The demo starts a temporary local server, sends real HTTP requests and shuts it down. It checks that a transfer succeeds, a retry produces no duplicate entry, a conflicting retry is rejected, and both balances still sum to zero. A failure returns a nonzero exit status.

For an interactive demo, start the server:

```bash
uvicorn ledgerflow.api:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000/docs** and try `POST /v1/transfers` with an `Idempotency-Key` header and this body:

```json
{"source": "cash", "destination": "merchant", "amount": "12.50"}
```

Retry with the same key: the `entry_id` stays the same. Change the amount while keeping the key: the API returns `400`. Inspect `GET /v1/audit` and `GET /v1/accounts/merchant/balance` to see the single transfer.

## What the implementation shows

- **Accounting invariant:** journal postings must sum to zero before a change is accepted.
- **Retry safety:** an idempotency key is bound to its original request, including the posting amounts.
- **Concurrency:** one in-process lock covers the idempotency check, journal update and balances; concurrent retries create one entry.
- **Separation of concerns:** `ledgerflow/domain.py` contains the ledger rules; `ledgerflow/api.py` translates HTTP input and errors.
- **Auditability:** frozen journal entries retain both sides of each accepted transfer in memory.

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Health check |
| `POST /v1/transfers` | Post or retry a transfer |
| `GET /v1/accounts/{account_id}/balance` | Read an account balance |
| `GET /v1/audit` | Inspect journal postings |

## Test

```bash
python -m pytest -q
ruff check .
ruff format --check .
python demo.py
```

The eight tests cover balanced postings, unbalanced-entry rejection, HTTP retries and conflicts, missing headers, invalid amounts and concurrent retries. The HTTP demo exercises a separately started server. GitHub Actions is configured at the **repository root**, in `.github/workflows/ledgerflow.yml`.

## Container option

```bash
docker compose up --build
```

The supplied image starts the API on port 8000. Container execution requires Docker; the Python tests and HTTP demo are the checks verified during preparation. No hosted deployment is claimed.

## Deliberate scope

This is an educational backend reference, not a banking service. State and idempotency records live in one process and are lost on restart. Use one worker; multiple processes do not share a ledger. There is no authentication, durable database, account ownership, overdraft policy, currency model or fixed currency rounding policy. Negative source balances are allowed. Python Decimal arithmetic uses its default precision; production money handling needs explicit precision, scale and currency rules. The audit log is immutable through the public domain API, not a tamper-proof store. Do not use real customer data or expose it publicly as a financial service.

## Author

Lakshay Atreja

[Portfolio status](../README.md) · [MIT licence](LICENSE)

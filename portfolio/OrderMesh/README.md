# OrderMesh

OrderMesh is a FastAPI order-orchestration service demonstrating explicit domain modelling, lifecycle validation, immutable-style event history, automated tests and container deployment.

## Highlights

- Order lifecycle: PENDING → CONFIRMED → FULFILLED, with pre-fulfilment cancellation
- Invalid transitions return HTTP 409
- Decimal-safe price calculations
- Duplicate order IDs are rejected
- Per-order event history
- FastAPI-generated OpenAPI documentation
- Pytest API/domain tests
- Docker packaging

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn pydantic
uvicorn ordermesh.api:app --reload
```

Visit `http://localhost:8000/docs`.

## Test

```bash
pip install pytest httpx
pytest -q
```

## API

- `POST /orders` — create an order
- `GET /orders/{id}` — fetch an order
- `POST /orders/{id}/confirm`
- `POST /orders/{id}/fulfill`
- `POST /orders/{id}/cancel`
- `GET /orders/{id}/events`
- `GET /health`

## Design

Business transition rules live in the domain model instead of route handlers. The service is intentionally small enough to run locally while preserving boundaries that can later be backed by PostgreSQL and an outbox/event broker.

## Next steps

PostgreSQL persistence, transactional outbox, Kafka/SQS adapter, OpenTelemetry and authentication.

MIT licensed. Built by Lakshay Atreja.

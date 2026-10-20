import asyncio

import httpx

from streamforge import api
from streamforge.engine import Event, StreamEngine


def test_ingest_validation_and_duplicate():
    async def exercise() -> None:
        api.engine = StreamEngine()
        transport = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            payload = {"id": "1", "key": "requests", "value": 10, "ts": 100}
            accepted = await client.post("/v1/events", json=payload)
            duplicate = await client.post("/v1/events", json=payload)
            invalid = await client.post("/v1/events", json={**payload, "id": ""})

        assert accepted.json()["status"] == "accepted"
        assert duplicate.json()["status"] == "duplicate"
        assert invalid.status_code == 422

    asyncio.run(exercise())


def test_out_of_order_eviction():
    engine = StreamEngine(window_seconds=10, allowed_lateness=2)
    engine.ingest(Event("new", "a", 10, 100))
    engine.ingest(Event("old", "a", 1000, 91))
    result = engine.ingest(Event("latest", "a", 20, 105))
    assert result["count"] == 2
    assert result["mean"] == 15


def test_spike_against_stable_baseline():
    engine = StreamEngine()
    for i in range(5):
        engine.ingest(Event(str(i), "a", 10, 100 + i))
    assert engine.ingest(Event("spike", "a", 100, 106))["anomaly"] is True

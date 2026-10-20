from streamforge.engine import Event, StreamEngine


def test_deduplication():
    e = StreamEngine()
    x = Event("1", "api", 10, 100)
    assert e.ingest(x)["status"] == "accepted"
    assert e.ingest(x)["status"] == "duplicate"


def test_late_event_policy():
    e = StreamEngine(window_seconds=10, allowed_lateness=2)
    e.ingest(Event("a", "k", 1, 100))
    assert e.ingest(Event("b", "k", 1, 80))["status"] == "too_late"

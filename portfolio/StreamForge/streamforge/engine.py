from collections import defaultdict
from dataclasses import dataclass
from math import isfinite, sqrt
from threading import RLock


@dataclass(frozen=True)
class Event:
    id: str
    key: str
    value: float
    ts: float


class StreamEngine:
    """Single-process event-time window. State is intentionally memory-only."""

    def __init__(self, window_seconds=60, allowed_lateness=10):
        if window_seconds <= 0 or allowed_lateness < 0:
            raise ValueError("invalid window configuration")
        self.window = window_seconds
        self.lateness = allowed_lateness
        self.seen = set()
        self.by_key = defaultdict(list)
        self.max_ts = float("-inf")
        self._lock = RLock()

    def ingest(self, e: Event):
        if not e.id or not e.key or not isfinite(e.value) or not isfinite(e.ts):
            raise ValueError("event requires identifiers and finite value/timestamp")
        with self._lock:
            if e.id in self.seen:
                return {"status": "duplicate"}
            self.max_ts = max(self.max_ts, e.ts)
            watermark = self.max_ts - self.lateness
            cutoff = watermark - self.window
            if e.ts < cutoff:
                return {"status": "too_late", "watermark": watermark}
            self.seen.add(e.id)
            # Out-of-order events require filtering beyond the oldest inserted item.
            for key in list(self.by_key):
                retained = [x for x in self.by_key[key] if x.ts >= cutoff]
                if retained:
                    self.by_key[key] = retained
                else:
                    del self.by_key[key]
            q = self.by_key[e.key]
            baseline = [x.value for x in q]
            q.append(e)
            vals = [x.value for x in q]
            mean = sum(vals) / len(vals)
            z = 0.0
            anomaly = False
            if len(baseline) >= 5:
                baseline_mean = sum(baseline) / len(baseline)
                sd = sqrt(
                    sum((x - baseline_mean) ** 2 for x in baseline) / len(baseline)
                )
                z = abs(e.value - baseline_mean) / sd if sd else 0.0
                anomaly = (sd == 0 and e.value != baseline_mean) or z >= 3.0
            return {
                "status": "accepted",
                "watermark": watermark,
                "count": len(vals),
                "mean": mean,
                "zscore": z,
                "anomaly": anomaly,
            }

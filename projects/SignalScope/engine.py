"""SignalScope: auditable, causal operational telemetry analysis.

All baselines are computed from past observations only. Scores and forecasts
are exploratory, not guarantees of production incident detection.
"""
from __future__ import annotations

from io import BytesIO
import json
import numpy as np
import pandas as pd

REQUIRED = {"timestamp", "service", "metric", "value"}
SEVERITY = {"Critical": 3, "High": 2, "Medium": 1, "Normal": 0}


def demo_data(days: int = 28, seed: int = 73) -> pd.DataFrame:
    """Reproducible multi-service telemetry with planted incidents and truth labels."""
    if days < 14:
        raise ValueError("Demo must include at least 14 days.")
    rng = np.random.default_rng(seed)
    stamps = pd.date_range("2026-09-01", periods=24 * days, freq="h", tz="UTC")
    services = ("Gateway", "Checkout", "Payments", "Search")
    records = []
    for service_idx, service in enumerate(services):
        for i, stamp in enumerate(stamps):
            h = stamp.hour
            peak = np.sin((h - 7) * 2 * np.pi / 24)
            weekday = 1.0 if stamp.dayofweek < 5 else .77
            base_req = (740 + service_idx * 120 + 160 * peak) * weekday
            measurements = {
                "requests_per_min": max(0.0, base_req + rng.normal(0, 23)),
                "latency_ms": max(0.0, 100 + service_idx * 18 + 21 * peak + rng.normal(0, 8)),
                "error_rate_pct": max(0.0, .55 + service_idx * .11 + rng.normal(0, .12)),
            }
            incident_a = 24 * 12 + 8 <= i < 24 * 12 + 14 and service in ("Checkout", "Payments")
            incident_b = 24 * 21 + 15 <= i < 24 * 21 + 20 and service in ("Gateway", "Search")
            if incident_a:
                measurements["latency_ms"] *= 2.9
                measurements["error_rate_pct"] += 5.5
                measurements["requests_per_min"] *= .64
            if incident_b:
                measurements["latency_ms"] *= 2.15
                measurements["error_rate_pct"] += 3.7
            for metric, value in measurements.items():
                records.append((stamp, service, metric, round(float(value), 3), bool(incident_a or incident_b)))
    return pd.DataFrame(records, columns=["timestamp", "service", "metric", "value", "known_incident"])


def parse_telemetry(source: bytes | pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Parse a long-format hourly CSV; return normalized data and quality diagnostics."""
    if isinstance(source, bytes):
        if len(source) > 12_000_000:
            raise ValueError("CSV exceeds the 12 MB upload limit.")
        try:
            data = pd.read_csv(BytesIO(source))
        except Exception as exc:
            raise ValueError("Could not parse CSV.") from exc
    elif isinstance(source, pd.DataFrame):
        data = source.copy()
    else:
        raise ValueError("Expected CSV bytes or a DataFrame.")
    data.columns = [str(x).strip().lower() for x in data.columns]
    if not REQUIRED.issubset(data.columns):
        raise ValueError("CSV must have timestamp, service, metric and value columns.")
    if not 1 <= len(data) <= 90_000:
        raise ValueError("Provide 1 to 90,000 rows.")
    data = data[list(REQUIRED) + (["known_incident"] if "known_incident" in data else [])].copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce", utc=True)
    data["value"] = pd.to_numeric(data["value"], errors="coerce")
    if data[["timestamp", "service", "metric", "value"]].isna().any().any():
        raise ValueError("Missing or invalid timestamps, service names, metrics or numeric values.")
    if not np.isfinite(data["value"].to_numpy(dtype=float)).all():
        raise ValueError("Nonfinite telemetry values are not supported.")
    for col in ("service", "metric"):
        data[col] = data[col].astype(str).str.strip().str.slice(0, 64)
        if (data[col] == "").any():
            raise ValueError("Service and metric names cannot be blank.")
    data["timestamp"] = data["timestamp"].dt.floor("h")
    if data["service"].nunique() > 40 or data["metric"].nunique() > 24:
        raise ValueError("Limit this demo to 40 services and 24 metrics.")
    if "known_incident" in data:
        truth = data["known_incident"].astype(str).str.lower().str.strip()
        if not truth.isin(["true", "false", "1", "0", "yes", "no"]).all():
            raise ValueError("known_incident must be boolean when provided.")
        data["known_incident"] = truth.isin(["true", "1", "yes"])
    duplicate_count = int(data.duplicated(["timestamp", "service", "metric"]).sum())
    agg = {"value": "median"}
    if "known_incident" in data:
        agg["known_incident"] = "max"
    data = data.groupby(["timestamp", "service", "metric"], as_index=False).agg(agg)
    data = data.sort_values(["service", "metric", "timestamp"]).reset_index(drop=True)
    gaps = []
    for (service, metric), grp in data.groupby(["service", "metric"], sort=True):
        missing = int(max(0, ((grp["timestamp"].max() - grp["timestamp"].min()) / pd.Timedelta(hours=1)) + 1 - len(grp)))
        if missing:
            gaps.append({"service": service, "metric": metric, "missing_hours": missing})
    quality = {
        "rows": len(data), "services": int(data["service"].nunique()),
        "metrics": int(data["metric"].nunique()), "duplicate_rows_aggregated": duplicate_count,
        "missing_hourly_intervals": int(sum(x["missing_hours"] for x in gaps)),
        "gaps_by_signal": gaps[:40], "has_truth_labels": "known_incident" in data,
        "aggregation_rule": "median for duplicate timestamp/service/metric combinations",
    }
    return data, quality


def score_telemetry(frame: pd.DataFrame, window: int = 72, threshold: float = 3.5) -> pd.DataFrame:
    """Causal median/MAD detector with adaptive hour-of-day baseline."""
    if not 24 <= window <= 336 or not 2 <= threshold <= 10:
        raise ValueError("Window must be 24..336 hours and threshold 2..10.")
    chunks = []
    for (service, metric), sub in frame.groupby(["service", "metric"], sort=True):
        sub = sub.sort_values("timestamp").copy()
        values = sub["value"].to_numpy(dtype=float)
        hours = sub["timestamp"].dt.hour.to_numpy()
        baseline = np.full(len(sub), np.nan)
        zscore = np.full(len(sub), np.nan)
        for i in range(min(window, 24), len(values)):
            hist = values[max(0, i - window):i]
            centre = float(np.median(hist))
            same_hour = values[max(0, i - 24 * 9):i]
            hour_mask = hours[max(0, i - 24 * 9):i] == hours[i]
            seasonal = float(np.median(same_hour[hour_mask])) if hour_mask.sum() >= 3 else centre
            expected = .45 * centre + .55 * seasonal
            mad = float(np.median(np.abs(hist - centre)))
            scale = max(1.4826 * mad, max(abs(centre) * .007, .025))
            baseline[i] = expected
            zscore[i] = (values[i] - expected) / scale
        sub["baseline"] = baseline
        sub["robust_score"] = zscore
        magnitude = np.abs(zscore)
        sub["alert"] = np.isfinite(magnitude) & (magnitude >= threshold)
        sub["severity"] = np.where(
            magnitude >= max(6.0, threshold + 2), "Critical",
            np.where(magnitude >= max(4.5, threshold + .7), "High",
                     np.where(sub["alert"], "Medium", "Normal")),
        )
        sub["direction"] = np.where(zscore >= 0, "Increase", "Decrease")
        chunks.append(sub)
    return pd.concat(chunks, ignore_index=True) if chunks else frame.copy()


def group_incidents(scored: pd.DataFrame, max_gap_hours: int = 2) -> pd.DataFrame:
    """Group related alert timestamps; hypotheses are explicitly non-causal."""
    alerts = scored.loc[scored["alert"]].sort_values("timestamp").copy()
    columns = ["incident_id", "start", "end", "duration_hours", "severity",
               "risk_score", "services", "signals", "alert_count", "first_observed_service"]
    if alerts.empty:
        return pd.DataFrame(columns=columns)
    groups = []
    batch = []
    prev = None
    for _, row in alerts.iterrows():
        if prev is not None and row["timestamp"] - prev > pd.Timedelta(hours=max_gap_hours):
            groups.append(pd.DataFrame(batch))
            batch = []
        batch.append(row.to_dict())
        prev = row["timestamp"]
    if batch:
        groups.append(pd.DataFrame(batch))
    out = []
    for number, g in enumerate(groups, 1):
        peak = float(np.abs(g["robust_score"]).max())
        severity = "Critical" if "Critical" in set(g["severity"]) else ("High" if "High" in set(g["severity"]) else "Medium")
        services = sorted(g["service"].unique().tolist())
        signals = sorted(g["metric"].unique().tolist())
        risk = min(100.0, round(12 * peak + 6 * (len(services) - 1) + 3 * (len(signals) - 1), 1))
        out.append({
            "incident_id": f"INC-{number:03d}", "start": g["timestamp"].min(),
            "end": g["timestamp"].max(),
            "duration_hours": int((g["timestamp"].max() - g["timestamp"].min()) / pd.Timedelta(hours=1) + 1),
            "severity": severity, "risk_score": risk,
            "services": ", ".join(services), "signals": ", ".join(signals),
            "alert_count": len(g),
            "first_observed_service": str(g.iloc[0]["service"]),
        })
    return pd.DataFrame(out).sort_values(["risk_score", "start"], ascending=[False, True]).reset_index(drop=True)


def forecast_next_day(frame: pd.DataFrame, service: str, metric: str) -> pd.DataFrame:
    """Hourly historical-pattern forecast with empirical 80% residual envelope."""
    sub = frame[(frame["service"] == service) & (frame["metric"] == metric)].sort_values("timestamp")
    if len(sub) < 72:
        raise ValueError("At least 72 hourly observations are required to forecast this signal.")
    values = sub["value"].to_numpy(dtype=float)
    hours = sub["timestamp"].dt.hour.to_numpy()
    recent = values[-min(len(values), 24 * 14):]
    recent_hours = hours[-len(recent):]
    group_baselines = {hour: float(np.median(recent[recent_hours == hour])) for hour in range(24)}
    residuals = recent - np.array([group_baselines[int(h)] for h in recent_hours])
    lo, hi = np.percentile(residuals, [10, 90])
    start = sub["timestamp"].max()
    dates = pd.date_range(start + pd.Timedelta(hours=1), periods=24, freq="h", tz="UTC")
    predictions = np.array([group_baselines[int(stamp.hour)] for stamp in dates], dtype=float)
    # Current pipeline targets non-negative business metrics; negative series retain negative forecasts.
    data = pd.DataFrame({"timestamp": dates, "forecast": predictions,
                         "lower_80": predictions + lo, "upper_80": predictions + hi})
    if (sub["value"] >= 0).all():
        for col in ("forecast", "lower_80", "upper_80"):
            data[col] = data[col].clip(lower=0)
    return data


def score_against_truth(scored: pd.DataFrame) -> dict | None:
    """Synthetic or user-supplied labels only, evaluated on observations with history."""
    if "known_incident" not in scored:
        return None
    valid = scored["robust_score"].notna()
    actual = scored.loc[valid, "known_incident"].astype(bool)
    predicted = scored.loc[valid, "alert"].astype(bool)
    tp = int((actual & predicted).sum())
    fp = int((~actual & predicted).sum())
    fn = int((actual & ~predicted).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {"evaluated_rows": int(valid.sum()), "true_positives": tp,
            "false_positives": fp, "false_negatives": fn,
            "precision": round(precision, 3), "recall": round(recall, 3),
            "f1": round(2 * precision * recall / (precision + recall), 3) if precision + recall else 0.0}


def export_report(incidents: pd.DataFrame, quality: dict, config: dict) -> bytes:
    """Shareable, reproducible investigation evidence with configuration and caveats."""
    safe_incidents = json.loads(incidents.to_json(orient="records", date_format="iso"))
    return json.dumps({
        "name": "SignalScope operational investigation", "configuration": config,
        "data_quality": quality, "incidents": safe_incidents,
        "interpretation": "Statistical flags are leads for analyst review, not confirmed root causes.",
    }, indent=2).encode("utf-8")

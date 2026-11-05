"""Pure functions for SignalScope, an explainable operations analytics prototype."""
from __future__ import annotations
from datetime import timedelta
import numpy as np
import pandas as pd


def demo_data(n: int = 120) -> pd.DataFrame:
    """Reproducible synthetic data, including three deliberately planted events."""
    rng = np.random.default_rng(2026)
    dates = pd.date_range(end=pd.Timestamp('2026-10-31'), periods=n, freq='D')
    weekday = np.where(dates.weekday < 5, 30.0, -22.0)
    values = 200 + np.arange(n) * 0.23 + weekday + rng.normal(0, 8, n)
    for idx, delta in [(n // 3, 120), (n // 2, -85), (n - 9, 140)]:
        values[idx] = max(0, values[idx] + delta)
    return pd.DataFrame({'date': dates, 'value': values.round(1)})


def parse_series(csv_bytes: bytes) -> pd.DataFrame:
    if len(csv_bytes) > 5_000_000:
        raise ValueError('Please upload a CSV smaller than 5 MB.')
    try:
        df = pd.read_csv(__import__('io').BytesIO(csv_bytes))
    except Exception as exc:
        raise ValueError('Unable to read CSV. Provide a date column and a numeric value column.') from exc
    df.columns = [str(c).strip().lower() for c in df.columns]
    date_key = next((c for c in ('date', 'day', 'timestamp') if c in df.columns), None)
    value_key = next((c for c in ('value', 'volume', 'demand', 'count', 'requests') if c in df.columns), None)
    if date_key is None or value_key is None:
        raise ValueError('Expected columns date,value (or day/timestamp and demand/volume/count/requests).')
    out = df[[date_key, value_key]].copy()
    out.columns = ['date', 'value']
    out['date'] = pd.to_datetime(out['date'], errors='coerce', utc=True).dt.tz_convert(None).dt.normalize()
    out['value'] = pd.to_numeric(out['value'], errors='coerce')
    if out.isna().any().any() or not np.isfinite(out['value'].to_numpy()).all():
        raise ValueError('Dates and values must be valid, finite and nonempty.')
    out = out.groupby('date', as_index=False)['value'].sum().sort_values('date').reset_index(drop=True)
    if not 14 <= len(out) <= 5000:
        raise ValueError('Please provide between 14 and 5,000 distinct dates.')
    if (out['value'] < 0).any():
        raise ValueError('This prototype expects non-negative volumes or counts.')
    # Deliberately do not fabricate missing dates. Warn in the interface instead.
    return out


def flag_anomalies(frame: pd.DataFrame, window: int = 21, threshold: float = 3.5) -> pd.DataFrame:
    """Causal rolling median and MAD; previous points only, no forward leakage."""
    if window < 7 or threshold <= 0:
        raise ValueError('Window must be at least 7 and threshold must be positive.')
    d = frame.sort_values('date').copy().reset_index(drop=True)
    observed = d['value'].to_numpy(dtype=float)
    expected = np.full(len(d), np.nan)
    scores = np.full(len(d), np.nan)
    for i in range(window, len(d)):
        history = observed[max(0, i - window):i]
        baseline = float(np.median(history))
        mad = float(np.median(np.abs(history - baseline)))
        scale = max(1.4826 * mad, 1.0)  # floor stabilises constant histories
        expected[i] = baseline
        scores[i] = (observed[i] - baseline) / scale
    d['expected'] = expected
    d['robust_score'] = scores
    d['alert'] = np.isfinite(scores) & (np.abs(scores) >= threshold)
    d['direction'] = np.where(d['robust_score'] >= 0, 'Spike', 'Drop')
    return d


def forecast_seven_days(frame: pd.DataFrame) -> pd.DataFrame:
    """Baseline weekday medians, plus a capped local linear trend. Not a learned ML model."""
    d = frame.sort_values('date').reset_index(drop=True)
    values = d['value'].to_numpy(dtype=float)
    end = pd.Timestamp(d['date'].iloc[-1])
    recent = d.tail(56).copy()
    x = np.arange(len(recent), dtype=float)
    slope = float(np.polyfit(x, recent['value'].to_numpy(dtype=float), 1)[0]) if len(recent) > 7 else 0.0
    cap = max(float(np.median(values)) * 0.03, 0.5)
    slope = float(np.clip(slope, -cap, cap))
    baseline = float(np.median(recent['value']))
    result = []
    for step in range(1, 8):
        next_date = end + timedelta(days=step)
        same_day = recent[recent['date'].dt.weekday == next_date.weekday()]['value']
        day_level = float(same_day.median()) if len(same_day) else baseline
        predicted = max(0.0, day_level + slope * step)
        result.append({'date': next_date, 'forecast': round(predicted, 1)})
    return pd.DataFrame(result)

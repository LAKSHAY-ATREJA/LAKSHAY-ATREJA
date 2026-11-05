# SignalScope — Operations Anomaly Monitor

A complete, browser-based, **non-RAG** applied analytics tool for operational time series. Upload daily CSV data, detect unexpected volume spikes/drops, review incidents, forecast next-week demand, and download a review report.

## What works
- CSV ingestion and validation (`date,value` with daily contiguous dates; demand/volume/count also accepted)
- Causal rolling-median/MAD anomaly detection with adjustable threshold/window
- Incident review queue with explainable robust scores
- Simple, interpretable seven-day trend/weekday projection
- Interactive SVG chart; export analysis as CSV
- Privacy by design: all processing stays in the browser; no API key or backend
- Deterministic synthetic demo data to reproduce anomaly scenarios

**Method honesty:** This is an explainable statistical prototype. It is **not** a trained neural-network model, a validated forecasting product or a real client deployment. Sample data and flags are illustrative.

## Run
```bash
python -m http.server 8080
# open http://localhost:8080/projects/SignalScope/ from repository root
```
Or, inside this folder: `python -m http.server 8080` then `http://localhost:8080`.

## Test
Node.js >=18; no dependencies:
```bash
node projects/SignalScope/tests.mjs
```

## CSV format
```csv
date,value
2026-10-01,120
2026-10-02,123
2026-10-03,117
```
At least seven days are required before anomaly scores are generated; more is preferable.

## Limitations and next steps
Weekly seasonality is not explicitly removed from anomaly scoring; strong weekly patterns may create false positives. Forecasts use robust weekday offsets and a capped ordinary-least-squares trend; production use would require holdout validation, monitoring, and domain-specific thresholds.

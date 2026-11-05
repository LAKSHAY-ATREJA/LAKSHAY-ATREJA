# SignalScope | Operations Intelligence Workbench

An evidence-focused incident investigation application for multi-service operational telemetry. Import hourly signals from CSV or explore a reproducible synthetic four-service environment. The workbench combines causal anomaly scoring, correlated incident triage, service impact analysis, a historical-pattern forecast with empirical uncertainty bands, and exportable investigation evidence.
---
LIVE DEMO : https://signalscope-acpquoscfzxf7q2reymsxm.streamlit.app/

## Engineering design

- **Causal detection:** historical rolling median and median absolute deviation, blended with an hour-of-day baseline. Every score uses earlier observations only.
- **Correlated incident triage:** group related service and metric alerts within a configurable time window, rank blast radius, and preserve the earliest observed signal as a lead rather than a claimed root cause.
- **Observability:** inspect measured vs expected signals, deviation scores, severity and time windows using interactive charts.
- **Forecasting:** 24-hour historical-pattern projection with an indicative empirical 10th–90th percentile residual envelope.
- **Quality controls:** timestamp normalization, duplicate aggregation, invalid-input rejection, missing-interval audits and reproducible synthetic fixtures.
- **Evaluation:** precision, recall and F1 against independently provided binary incident labels. In the built-in demo, the ground truth comes only from planted synthetic incidents.
- **Evidence exports:** scored telemetry CSV, forecast CSV, structured incident investigation JSON with methodology/configuration.

## Run the application

In Streamlit Community Cloud, choose repository `LAKSHAY-ATREJA/LAKSHAY-ATREJA`, branch `main`, main file `projects/SignalScope/app.py`. Public live-demo URL will be linked here only after deployment has been verified.

Locally, from repository root:

```bash
pip install -r projects/SignalScope/requirements.txt
streamlit run projects/SignalScope/app.py
```

The Streamlit app imports `engine.py` from its own directory. No secrets, external API or database are required.

## CSV contract

```csv
timestamp,service,metric,value
2026-10-01T00:00:00Z,Checkout,latency_ms,140.1
2026-10-01T01:00:00Z,Checkout,latency_ms,151.4
2026-10-01T00:00:00Z,Checkout,error_rate_pct,0.7
```

An optional `known_incident` boolean allows labelled detection evaluation. Timestamps are normalized to UTC and hourly precision. Rows with duplicate timestamp/service/metric keys are aggregated using their median values, and gaps are surfaced rather than fabricated.

## Tests

```bash
pip install -r projects/SignalScope/requirements.txt
cd projects/SignalScope
python -m unittest discover -p "test_*.py" -v
```

CI runs unit tests and checks that the Streamlit server starts successfully.

## Scope and honesty

This is a research and engineering **portfolio prototype**, not a commercial monitoring platform, production-tested anomaly detector or causal inference engine. Risk ranks are heuristic. Synthetic incident evaluation should not be presented as validation on real customers or infrastructure. Forecast intervals are descriptive residual envelopes and have no guaranteed coverage. The app processes uploads on the Streamlit host; never upload confidential telemetry to a public deployment.

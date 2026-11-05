"""SignalScope | Operations Intelligence Workbench."""
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from engine import (demo_data, parse_telemetry, score_telemetry, group_incidents,
                    forecast_next_day, score_against_truth, export_report)

st.set_page_config(page_title="SignalScope | Operations Intelligence", page_icon="📡", layout="wide")
st.markdown("""
<style>
.block-container {max-width: 1330px; padding-top: 2rem;}
h1,h2,h3 {letter-spacing: -.03em;}
[data-testid="stMetric"] {background: rgba(128,135,160,.08); border: 1px solid rgba(135,143,165,.16);
 border-radius: 12px; padding: 14px 18px;}
div[data-testid="stAlert"] {border-radius: 10px;}
</style>""", unsafe_allow_html=True)

st.caption("OPERATIONS ENGINEERING  /  OPEN DEMONSTRATION")
st.title("SignalScope")
st.write("An incident investigation workbench for noisy multi-service telemetry. Detect unusual behaviour, assess blast radius, inspect evidence, and export an auditable incident report.")
st.info("Reproducible synthetic incidents are loaded by default. The detector uses causal robust statistics, not a trained ML model. Flags are hypotheses, not confirmed root causes.")

with st.sidebar:
    st.header("Investigation setup")
    uploaded = st.file_uploader("Hourly telemetry CSV", type=["csv"], help="Columns: timestamp, service, metric, value. Optional known_incident for labelled evaluation.")
    st.caption("No upload needed. The built-in four-service dataset contains planted disruptions.")
    st.divider()
    window = st.slider("Historical baseline window (hours)", 24, 168, 72, step=24)
    threshold = st.slider("Detection sensitivity (robust z-score)", 2.0, 8.0, 3.5, .25)
    max_gap = st.slider("Correlate alerts within (hours)", 1, 6, 2)
    st.caption("Baselines reference preceding observations only. Uploaded data is processed by the hosting server; avoid confidential datasets.")

@st.cache_data(show_spinner="Analysing telemetry...")
def analyse(data: bytes | None, window: int, threshold: float, gap: int):
    raw, quality = parse_telemetry(data if data is not None else demo_data())
    scored = score_telemetry(raw, window=window, threshold=threshold)
    incidents = group_incidents(scored, max_gap_hours=gap)
    backtest = score_against_truth(scored)
    return raw, quality, scored, incidents, backtest

try:
    raw, quality, scored, incidents, backtest = analyse(uploaded.getvalue() if uploaded else None, window, threshold, max_gap)
except (ValueError, pd.errors.ParserError) as exc:
    st.error(f"Telemetry could not be analysed: {exc}")
    st.stop()

m1,m2,m3,m4 = st.columns(4)
m1.metric("Observed signals", f"{len(raw):,}")
m2.metric("Services monitored", quality["services"])
m3.metric("Alert observations", f"{int(scored.alert.sum()):,}")
m4.metric("Incident clusters", len(incidents))
tabs = st.tabs(["Operations overview", "Incident investigation", "Signal explorer", "Forecast & evaluation", "Data quality / exports"])

with tabs[0]:
    st.subheader("Incident portfolio")
    st.caption("Risk scores combine anomalous deviation and breadth across impacted services and metrics. They are heuristic triage indicators.")
    if incidents.empty:
        st.success("No incident clusters at current sensitivity.")
    else:
        st.dataframe(incidents, hide_index=True, use_container_width=True,
                     column_config={"risk_score": st.column_config.ProgressColumn("Triage score", min_value=0, max_value=100)})
    st.subheader("Service impact summary")
    counts = scored[scored.alert].groupby("service").size().rename("alerts")
    table = pd.DataFrame({"service": sorted(raw.service.unique())})
    table["alerts"] = table["service"].map(counts).fillna(0).astype(int)
    st.bar_chart(table.set_index("service"), use_container_width=True)
    st.caption("This is an observational summary; simultaneous alerts do not prove causal relationships.")

with tabs[1]:
    st.subheader("Evidence-led investigation")
    if incidents.empty:
        st.warning("No detected incidents to investigate. Adjust sensitivity or use sample data.")
    else:
        selected = st.selectbox("Choose incident", incidents["incident_id"].tolist(),
                                format_func=lambda x: f"{x}  |  {incidents.loc[incidents.incident_id==x, 'severity'].iloc[0]}")
        incident = incidents[incidents.incident_id==selected].iloc[0]
        start = incident["start"] - pd.Timedelta(hours=3)
        end = incident["end"] + pd.Timedelta(hours=3)
        relevant = scored[(scored.timestamp >= start) & (scored.timestamp <= end)]
        a,b,c = st.columns(3)
        a.metric("Severity", incident["severity"])
        b.metric("Impacted services", len(incident["services"].split(", ")))
        c.metric("Observed duration", f"{incident['duration_hours']} h")
        st.write(f"**Earliest observed alert:** {incident['first_observed_service']} (hypothesis only)")
        st.dataframe(relevant.loc[relevant.alert, ["timestamp", "service", "metric", "value", "baseline", "robust_score", "severity", "direction"]].sort_values("robust_score", key=abs, ascending=False),
                     hide_index=True, use_container_width=True)
        st.caption("Compare concurrent indicators and timestamps to investigate potential contributing services. This interface does not claim automated root-cause proof.")

with tabs[2]:
    st.subheader("Explore a signal")
    c1,c2 = st.columns(2)
    service = c1.selectbox("Service", sorted(raw.service.unique()))
    metric = c2.selectbox("Metric", sorted(raw.metric.unique()))
    signal = scored[(scored.service == service) & (scored.metric == metric)].sort_values("timestamp")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=signal.timestamp, y=signal.value, name="Observed", mode="lines", line=dict(color="#38bdf8", width=2)))
    fig.add_trace(go.Scatter(x=signal.timestamp, y=signal.baseline, name="Causal expected", mode="lines", line=dict(color="#f59e0b", dash="dot")))
    flags = signal[signal.alert]
    fig.add_trace(go.Scatter(x=flags.timestamp, y=flags.value, name="Detected anomaly", mode="markers", marker=dict(size=10, color="#fb7185", symbol="diamond")))
    fig.update_layout(height=460, hovermode="x unified", margin=dict(l=10,r=10,t=20,b=30), xaxis_title="UTC", yaxis_title=metric)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(signal.tail(50)[["timestamp","value","baseline","robust_score","severity"]].sort_values("timestamp", ascending=False), hide_index=True, use_container_width=True)

with tabs[3]:
    st.subheader("Next 24-hour indicative forecast")
    service_forecast = st.selectbox("Forecast service", sorted(raw.service.unique()), key="forecast_service")
    metric_forecast = st.selectbox("Forecast metric", sorted(raw.metric.unique()), key="forecast_metric")
    try:
        forecast = forecast_next_day(raw, service_forecast, metric_forecast)
        f = go.Figure()
        f.add_trace(go.Scatter(x=forecast.timestamp, y=forecast.upper_80, mode="lines", line=dict(width=0), showlegend=False))
        f.add_trace(go.Scatter(x=forecast.timestamp, y=forecast.lower_80, mode="lines", fill="tonexty", fillcolor="rgba(56,189,248,.15)", line=dict(width=0), name="Empirical 10th–90th percentile"))
        f.add_trace(go.Scatter(x=forecast.timestamp, y=forecast.forecast, mode="lines+markers", line=dict(color="#38bdf8"), name="Hourly seasonal median"))
        f.update_layout(height=330, xaxis_title="UTC", yaxis_title=metric_forecast, margin=dict(l=10,r=10,t=20,b=30))
        st.plotly_chart(f, use_container_width=True)
        st.caption("The uncertainty band comes from historical in-sample residuals and is not a validated probabilistic coverage guarantee.")
        st.download_button("Export forecast CSV", forecast.to_csv(index=False).encode(), "signalscope_forecast.csv", "text/csv")
    except ValueError as exc:
        st.warning(str(exc))
    st.divider()
    st.subheader("Detection performance")
    if backtest:
        a,b,c = st.columns(3)
        a.metric("Precision", f"{backtest['precision']:.1%}")
        b.metric("Recall", f"{backtest['recall']:.1%}")
        c.metric("F1", f"{backtest['f1']:.2f}")
        st.caption("Calculated only from provided truth labels. Default labels correspond to intentionally planted incidents in synthetic data, not a real-world benchmark.")
    else:
        st.info("Upload a CSV with a known_incident boolean column to evaluate alert detection against your own labelled events.")

with tabs[4]:
    st.subheader("Input quality and reproducibility")
    a,b,c = st.columns(3)
    a.metric("Duplicate records aggregated", quality["duplicate_rows_aggregated"])
    b.metric("Missing hourly intervals", quality["missing_hourly_intervals"])
    c.metric("Unique metrics", quality["metrics"])
    if quality["gaps_by_signal"]:
        st.dataframe(pd.DataFrame(quality["gaps_by_signal"]), hide_index=True, use_container_width=True)
    st.json({"window_hours":window,"threshold":threshold,"incident_gap_hours":max_gap,"data_quality":quality})
    st.download_button("Download scored telemetry CSV", scored.to_csv(index=False).encode(), "signalscope_scored.csv", "text/csv")
    st.download_button("Download investigation evidence (JSON)",
        export_report(incidents, quality, {"window_hours":window,"threshold":threshold,"incident_gap_hours":max_gap}),
        "signalscope_incidents.json", "application/json")
    st.caption("Only the downloaded report is generated; this application does not send data to an LLM or external telemetry service.")

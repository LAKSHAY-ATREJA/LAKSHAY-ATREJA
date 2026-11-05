"""SignalScope: live incident command centre and telemetry investigation UI."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from engine import (demo_data, parse_telemetry, score_telemetry, group_incidents,
                    forecast_next_day, score_against_truth, export_report)

st.set_page_config(page_title="SignalScope | Incident Command Centre", page_icon="📡", layout="wide")
st.markdown("""
<style>
.block-container{max-width:1480px;padding-top:1.3rem;padding-bottom:4rem}
h1,h2,h3{letter-spacing:-.04em}
h1{font-weight:800!important;font-size:3.2rem!important}
[data-testid="stMetric"]{border-radius:15px;border:1px solid rgba(125,155,184,.23);
background:linear-gradient(135deg,rgba(35,107,161,.14),rgba(88,106,130,.025));
padding:16px 18px;min-height:118px}
[data-testid="stMetricValue"]{font-size:1.9rem}
div[data-testid="stTabs"] button{font-weight:650}
[data-testid="stDataFrame"]{border-radius:12px}
.kicker{font-size:.75rem;color:#54b9fa;letter-spacing:.18em;font-weight:700}
.hero{max-width:1050px;color:#a2b3c6;font-size:1.045rem;line-height:1.62}
.pill{display:inline-block;border:1px solid rgba(70,168,212,.25);border-radius:80px;
background:rgba(70,160,220,.09);padding:6px 11px;margin:0 9px 10px 0;
font-size:.78rem;color:#87caff}
.section-kicker{font-size:.75rem;color:#6eabc7;letter-spacing:.1em;text-transform:uppercase}
</style>
""",unsafe_allow_html=True)

st.markdown('<div class="kicker">OPERATIONS ANALYTICS / INCIDENT ENGINEERING</div>',unsafe_allow_html=True)
st.title("SignalScope  |  Command Centre")
st.markdown('<p class="hero">Investigate what broke, when it happened and how far it spread. '
            'Observe real telemetry signals, correlate unusual activity across services, and '
            'export reproducible evidence for incident review.</p>',unsafe_allow_html=True)
st.markdown('<span class="pill">Multi-service correlation</span>'
            '<span class="pill">Causal anomaly detection</span>'
            '<span class="pill">Incident evidence</span>'
            '<span class="pill">Forecasts and evaluation</span>',unsafe_allow_html=True)

with st.sidebar:
    st.header("Analysis controls")
    upload=st.file_uploader("Import hourly telemetry CSV",type="csv",
        help="Required: timestamp,service,metric,value. Optional: known_incident")
    st.caption("Leave this empty to explore a four-service environment with reproducible sample incidents.")
    st.divider()
    window=st.slider("Baseline history (hours)",24,168,72,step=24)
    threshold=st.slider("Robust anomaly threshold",2.0,8.0,3.5,.25)
    gap=st.slider("Incident correlation window (hours)",1,6,2)
    st.divider()
    st.caption("Analytical methods: causal robust statistics, seasonal baselines, "
               "temporal alert grouping, heuristic triage and empirical residual intervals.")
    st.caption("No external model or API key required. Public hosting processes uploads server-side.")

@st.cache_data(show_spinner="Computing signals and incident groups...",max_entries=8)
def analyse(upload_bytes,window,threshold,gap):
    raw,quality=parse_telemetry(upload_bytes if upload_bytes is not None else demo_data())
    scored=score_telemetry(raw,window,threshold)
    incidents=group_incidents(scored,gap)
    evaluation=score_against_truth(scored)
    return raw,quality,scored,incidents,evaluation

try:
    raw,quality,scored,incidents,evaluation=analyse(upload.getvalue() if upload else None,
                                                   window,threshold,gap)
except (ValueError,pd.errors.ParserError) as exc:
    st.error(f"Could not analyse telemetry: {exc}")
    st.stop()

col1,col2,col3,col4=st.columns(4)
col1.metric("Services monitored",quality["services"])
col2.metric("Signals processed",f"{len(scored):,}")
col3.metric("Anomalous observations",int(scored["alert"].sum()))
col4.metric("Correlated incidents",len(incidents))
st.caption("DEMONSTRATION ENVIRONMENT" if upload is None else "IMPORTED TELEMETRY"
           + "   |   Alerts are statistical indicators, not confirmed production outages.")

tabs=st.tabs(["01  Mission control","02  Incident timeline","03  Signal explorer",
              "04  Forecast lab","05  Evidence centre"])

COLOURS={"Critical":"#fb7185","High":"#f59e0b","Medium":"#38bdf8"}

with tabs[0]:
    left,right=st.columns([1.65,1],gap="large")
    with left:
        st.subheader("Activity across the service estate")
        st.caption("A live representation of the selected dataset. Coloured markers indicate abnormal signal observations.")
        timeline=(scored[scored.alert].groupby(scored[scored.alert].timestamp.dt.floor("h"))
                  .size().rename("alerts").reset_index())
        counts=timeline.set_index("timestamp") if not timeline.empty else pd.DataFrame(columns=["alerts"])
        hourly=pd.date_range(scored.timestamp.min(),scored.timestamp.max(),freq="h")
        full=pd.Series(0,index=hourly,dtype=int)
        if not counts.empty:
            full.loc[counts.index.intersection(full.index)]=counts.reindex(full.index,fill_value=0)["alerts"]
        figure=go.Figure()
        figure.add_trace(go.Scatter(x=full.index,y=full.values,name="Alert events",mode="lines",
                                    fill="tozeroy",line=dict(color="#38bdf8",width=2),
                                    fillcolor="rgba(56,189,248,.12)"))
        if not incidents.empty:
            for _,row in incidents.head(8).iterrows():
                figure.add_vrect(x0=row["start"],x1=row["end"],line_width=0,
                                 fillcolor="rgba(251,113,133,.12)")
        figure.update_layout(height=365,hovermode="x unified",showlegend=False,
                             margin=dict(l=12,r=12,t=18,b=20),
                             xaxis_title="Timeline (UTC)",yaxis_title="Triggered alerts")
        st.plotly_chart(figure,use_container_width=True)
        st.markdown('<div class="section-kicker">Blast radius by service</div>',unsafe_allow_html=True)
        service_counts=(scored[scored.alert].groupby("service").size().reindex(
            sorted(raw.service.unique()),fill_value=0).sort_values(ascending=True))
        impact=go.Figure(go.Bar(y=service_counts.index,x=service_counts.values,
                                  orientation="h",marker_color="#4aa8e0"))
        impact.update_layout(height=240,margin=dict(l=5,r=10,t=5,b=10),
                             xaxis_title="Abnormal observations",yaxis_title="")
        st.plotly_chart(impact,use_container_width=True)
    with right:
        st.subheader("Incident priority queue")
        if incidents.empty:
            st.success("No incident groups detected at the selected sensitivity.")
        else:
            for _,inc in incidents.head(5).iterrows():
                color=COLOURS.get(inc["severity"],"#38bdf8")
                st.markdown(
                    "<div style='padding:14px 16px;border:1px solid rgba(132,158,183,.19);"
                    "border-left:4px solid "+color+";border-radius:10px;margin-bottom:10px;"
                    "background:rgba(103,120,157,.05)'>"
                    "<span style='font-weight:800'>"+inc["incident_id"]+"</span>"
                    "<span style='float:right;color:"+color+";font-weight:700'>"+inc["severity"]+"</span>"
                    "<div style='font-size:.85rem;margin-top:7px'>"+inc["services"]+"</div>"
                    "<div style='font-size:.77rem;opacity:.75;margin-top:6px'>"
                    +str(inc["alert_count"])+" flagged observations | risk index "
                    +str(inc["risk_score"])+"/100</div></div>",
                    unsafe_allow_html=True)
        st.caption("The risk index is a heuristic triage ranking, not a probabilistic severity measure.")
    st.divider()
    st.subheader("Service health matrix")
    st.caption("Heatmap of alert counts. Select another threshold in the sidebar to see the ranking change.")
    m=(scored[scored.alert].groupby(["service","metric"]).size().unstack(fill_value=0))
    m=m.reindex(index=sorted(raw.service.unique()),columns=sorted(raw.metric.unique()),fill_value=0)
    fig=go.Figure(data=go.Heatmap(z=m.values,x=m.columns,y=m.index,
                                  colorscale=[[0,"#122437"],[.35,"#1c89b7"],[.7,"#f59e0b"],[1,"#ef476f"]],
                                  hovertemplate="Service: %{y}<br>Metric: %{x}<br>Alerts: %{z}<extra></extra>"))
    fig.update_layout(height=275,margin=dict(l=10,r=10,t=10,b=10))
    st.plotly_chart(fig,use_container_width=True)

with tabs[1]:
    st.subheader("Investigate a correlated incident")
    if incidents.empty:
        st.warning("No incidents to investigate. Select sample data or lower the anomaly threshold.")
    else:
        selection=st.selectbox("Choose an incident",incidents["incident_id"].tolist(),
            format_func=lambda x: x+"  |  "+str(incidents.loc[incidents.incident_id==x,"severity"].iloc[0]))
        inc=incidents[incidents.incident_id==selection].iloc[0]
        a,b,c,d=st.columns(4)
        a.metric("Severity",inc["severity"])
        b.metric("Triage risk",f"{inc['risk_score']:.0f}/100")
        c.metric("Services affected",len(inc["services"].split(", ")))
        d.metric("Observed duration",f"{inc['duration_hours']}h")
        st.write("**Impact window:**",str(inc["start"]),"to",str(inc["end"]))
        st.info("First observed service: "+inc["first_observed_service"]
                +". This is a lead for investigation, not a proven root cause.")
        evidence=scored[(scored.timestamp>=inc["start"]-pd.Timedelta(hours=3))&
                        (scored.timestamp<=inc["end"]+pd.Timedelta(hours=3))&
                        (scored.alert)].copy()
        st.dataframe(evidence[["timestamp","service","metric","value","baseline",
                               "robust_score","direction","severity"]]
                     .sort_values("robust_score",key=abs,ascending=False),
                     hide_index=True,use_container_width=True)
        st.download_button("Export this incident evidence",
                           evidence.to_csv(index=False).encode(),
                           selection.lower()+"_evidence.csv","text/csv")

with tabs[2]:
    st.subheader("Inspect the measurement trail")
    a,b=st.columns(2)
    service=a.selectbox("Service",sorted(raw.service.unique()))
    metric=b.selectbox("Metric",sorted(raw.metric.unique()))
    sample=scored[(scored.service==service)&(scored.metric==metric)].sort_values("timestamp")
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=sample.timestamp,y=sample.value,mode="lines",name="Observed",
                             line=dict(color="#3cc0fa",width=2.1)))
    fig.add_trace(go.Scatter(x=sample.timestamp,y=sample.baseline,mode="lines",name="Historical expectation",
                             line=dict(color="#fbbf24",width=1.6,dash="dot")))
    abnormal=sample[sample.alert]
    fig.add_trace(go.Scatter(x=abnormal.timestamp,y=abnormal.value,mode="markers",
                             name="Flagged",marker=dict(color="#fb7185",symbol="diamond",size=10)))
    fig.update_layout(height=450,hovermode="x unified",
                      margin=dict(l=10,r=10,t=18,b=25),xaxis_title="UTC",yaxis_title=metric)
    st.plotly_chart(fig,use_container_width=True)
    st.caption("Only prior observations form a baseline. Unscored warm-up history is left blank rather than fabricated.")
    st.dataframe(sample.tail(60)[["timestamp","value","baseline","robust_score","severity"]]
                 .sort_values("timestamp",ascending=False),use_container_width=True,hide_index=True)

with tabs[3]:
    st.subheader("Next-day forecasting and validation")
    a,b=st.columns(2)
    forecast_service=a.selectbox("Forecast service",sorted(raw.service.unique()),key="f-service")
    forecast_metric=b.selectbox("Forecast metric",sorted(raw.metric.unique()),key="f-metric")
    try:
        forecast=forecast_next_day(raw,forecast_service,forecast_metric)
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=forecast.timestamp,y=forecast.upper_80,mode="lines",
                                 line=dict(width=0),showlegend=False))
        fig.add_trace(go.Scatter(x=forecast.timestamp,y=forecast.lower_80,mode="lines",
                                 line=dict(width=0),fill="tonexty",
                                 fillcolor="rgba(53,177,224,.19)",name="Empirical residual band"))
        fig.add_trace(go.Scatter(x=forecast.timestamp,y=forecast.forecast,mode="lines+markers",
                                 line=dict(color="#38bdf8",width=2),name="Hourly median estimate"))
        fig.update_layout(height=345,margin=dict(l=10,r=10,t=15,b=25),xaxis_title="UTC",
                          yaxis_title=forecast_metric)
        st.plotly_chart(fig,use_container_width=True)
        st.caption("The 10th–90th percentile historical residual envelope is illustrative; it is not a validated confidence interval.")
        st.download_button("Download forecast",forecast.to_csv(index=False).encode(),
                           "signalscope_forecast.csv","text/csv")
    except ValueError as exc:
        st.warning(str(exc))
    st.divider()
    st.subheader("Known-incident detection performance")
    if evaluation:
        a,b,c=st.columns(3)
        a.metric("Precision",f"{evaluation['precision']:.0%}")
        b.metric("Recall",f"{evaluation['recall']:.0%}")
        c.metric("F1 score",f"{evaluation['f1']:.2f}")
        st.caption("Default evaluation labels are synthetic planted outages, not measured real-world precision.")
    else:
        st.info("Add a known_incident boolean column to evaluate this detector using labelled telemetry.")

with tabs[4]:
    st.subheader("Quality controls and audit trail")
    a,b,c=st.columns(3)
    a.metric("Aggregated duplicate records",quality["duplicate_rows_aggregated"])
    b.metric("Unobserved hourly intervals",quality["missing_hourly_intervals"])
    c.metric("Monitored metric types",quality["metrics"])
    if quality["gaps_by_signal"]:
        st.dataframe(pd.DataFrame(quality["gaps_by_signal"]),hide_index=True,use_container_width=True)
    st.json({"analysis_config":{"window_hours":window,"robust_threshold":threshold,
                               "correlation_gap_hours":gap},"quality":quality})
    st.download_button("Download scored observations",scored.to_csv(index=False).encode(),
                       "signalscope_scored.csv","text/csv")
    st.download_button("Download reproducible incident report",
                       export_report(incidents,quality,
                           {"window_hours":window,"threshold":threshold,"gap_hours":gap}),
                       "signalscope_incident_report.json","application/json")
    st.caption("This workbench does not send uploaded telemetry to an LLM or external monitoring API.")

"""SignalScope Streamlit demo: reproducible, free of API keys and external calls."""
import pandas as pd
import streamlit as st
from logic import demo_data, parse_series, flag_anomalies, forecast_seven_days

st.set_page_config(page_title='SignalScope | Operations Analytics', page_icon='📈', layout='wide')
st.title('SignalScope')
st.caption('Operations anomaly monitoring and transparent short-term forecasting | Streamlit demo')
st.info('Portfolio prototype using robust statistics, not a trained prediction model. Demo data is synthetic. No files are sent to an external model.')

with st.sidebar:
    st.header('Data and controls')
    upload = st.file_uploader('Upload daily CSV', type=['csv'], help='Columns: date,value. Also accepts volume, demand, count or requests.')
    window = st.slider('Rolling history (days)', 7, 45, 21)
    sensitivity = st.slider('Anomaly threshold (robust score)', 2.0, 6.0, 3.2, 0.1)
    st.markdown('**Try it immediately:** The generated demo already contains three planted anomalies.')

try:
    raw = parse_series(upload.getvalue()) if upload is not None else demo_data()
    result = flag_anomalies(raw, window, sensitivity)
    projection = forecast_seven_days(raw)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

missing = (raw['date'].diff().dt.days.fillna(1) > 1).sum()
if missing:
    st.warning(f'{missing} gap(s) in dates. Results use available observations, without imputing missing days.')

left, middle, right = st.columns(3)
left.metric('Observations', len(result))
middle.metric('Flagged events', int(result['alert'].sum()))
right.metric('Next 7-day projected total', f"{projection['forecast'].sum():,.0f}")

st.subheader('Operational signal')
plot = result.set_index('date')[['value', 'expected']].rename(columns={'value': 'Observed', 'expected': 'Rolling median'})
st.line_chart(plot, use_container_width=True)
st.caption('Baseline uses only earlier observations. Initial history is unscored; anomaly detection begins after the selected rolling window.')

st.subheader('Review alerts')
alerts = result.loc[result['alert'], ['date', 'value', 'expected', 'robust_score', 'direction']].copy()
alerts['robust_score'] = alerts['robust_score'].round(2)
alerts['expected'] = alerts['expected'].round(1)
if alerts.empty:
    st.success('No events crossed the selected threshold.')
else:
    st.dataframe(alerts.sort_values('date', ascending=False), hide_index=True, use_container_width=True)

st.subheader('Seven-day indicative forecast')
st.line_chart(projection.set_index('date'), use_container_width=True)
st.caption('Simple weekday-median forecast with capped local trend. For illustration, not operational planning or guaranteed demand forecasts.')

c1, c2 = st.columns(2)
with c1:
    st.download_button('Download scored data CSV', result.to_csv(index=False).encode(), 'signalscope_scored.csv', 'text/csv')
with c2:
    st.download_button('Download forecast CSV', projection.to_csv(index=False).encode(), 'signalscope_forecast.csv', 'text/csv')

with st.expander('What this demonstrates'):
    st.write('CSV ingestion, validation, explainable causal anomaly scoring, configurable analyst thresholds, a seven-day statistical forecast, charts, and downloadable results.')
    st.write('Technical approach: Python, pandas, NumPy and Streamlit. No LLM, RAG, external services or API keys are used.')

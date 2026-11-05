# SignalScope | Operations Anomaly Monitoring

A Streamlit-ready, **non-RAG** applied analytics dashboard. Bring your own `date,value` CSV or use a synthetic demo. Explore unusual demand or traffic events, review explainable rolling-median/MAD scores, see a transparent seven-day statistical forecast, and download results.

## Streamlit demo

**Deploy from GitHub:** In [Streamlit Community Cloud](https://share.streamlit.io/) choose repository `LAKSHAY-ATREJA/LAKSHAY-ATREJA`, branch `main`, main file `projects/SignalScope/app.py`. The dependency file is `projects/SignalScope/requirements.txt`.

There is **no claimed live-demo URL until the deployment has actually been created and checked.**

## Features
- CSV validation and synthetic demonstration data with intentional anomaly events
- Causal rolling median / median absolute deviation scoring, configurable rolling window and alert threshold
- Review alerts with scores and directions
- Weekday median + capped trend forecast over seven days
- Interactive charts, downloads, no third-party API keys

## Local run

```bash
pip install -r projects/SignalScope/requirements.txt
streamlit run projects/SignalScope/app.py
```

## Tests

```bash
cd projects/SignalScope
python -m unittest test_logic.py
```

## Method and limits

The app uses robust **statistics**, not a machine-learning model, and does not make guarantees about future demand. The demo data is synthetic, the forecast is illustrative, and gaps in user datasets are not imputed. Work is done in the app process; Streamlit may handle uploaded files on its hosting infrastructure, so do not upload confidential information.

The folder also retains an earlier JavaScript/browser demo (`index.html`, `logic.mjs`, `tests.mjs`). The Python Streamlit implementation is independently runnable.

# NIFTY 50 | Market Intelligence

**[▶ Explore the hosted NIFTY 50 dashboard](https://gpm7jvk6pbxncjfun9my9r.streamlit.app/)**

A market research dashboard developed from my original Python/Streamlit Nifty 50 screener. It retains the original features—**MACD Buy/Sell indicator states**, **distance to one-year highs**, and **NSE RSS corporate announcements**—and presents them as an interactive analyst workspace with candlestick and volume charts, RSI, market breadth, signal filters, watchlist ranking, downloadable reports and an opt-in Yahoo Finance data source.

> **Demo tip:** The dashboard starts with clearly labelled synthetic example data so you can explore the interface without credentials. Select the Yahoo Finance source in the sidebar to request historical market data. Hosted availability depends on Streamlit Community Cloud.

## Dashboard features

| Workspace | Features |
| --- | --- |
| **Market pulse** | Momentum scatterplot, signal breakdown, gainers/losers and summary KPIs |
| **Momentum terminal** | Last-session MACD screeners, crossover indicators, 130-session OHLC candlesticks, moving averages, trading volume, MACD histogram and recent six-session history |
| **52-week gap analysis** | Price-vs-high deviation rankings, rolling high/low information, volatility and CSV export |
| **NSE announcements** | On-demand RSS reading, announcement search, source links and export without unattended PDF downloading |
| **Data quality** | Observed sessions, source labeling, missing-ticker diagnostics and reproducible screener export |

### Instant demo versus live market data

The app **opens immediately using clearly labelled synthetic price data**, generated deterministically for the original 50-ticker watchlist. This is intended to show the UI and test it without API credentials. It **does not represent real historical prices**.

Select **Yahoo Finance · live prices** in the sidebar to request genuine historical price data. This external service can be delayed, unavailable, rate-limited or return incomplete ticker coverage. The dashboard displays failures; it never silently replaces missing live prices with generated ones. The 50-symbol watchlist comes from the original user-supplied project and is **not represented as the latest official index membership**.

## Deploy on Streamlit Community Cloud

1. Open **[Streamlit Community Cloud](https://share.streamlit.io/)** and sign in with GitHub.
2. Choose **Create app → Yup, I have an app → Paste GitHub URL**.
3. Paste the entrypoint link:

   `https://github.com/LAKSHAY-ATREJA/LAKSHAY-ATREJA/blob/main/projects/Nifty50-Market-Intelligence/app.py`

Or enter these exact values:

| Field | Value |
| --- | --- |
| Repository | `LAKSHAY-ATREJA/LAKSHAY-ATREJA` |
| Branch | `main` |
| Main file path | `projects/Nifty50-Market-Intelligence/app.py` |
| Optional app subdomain | `nifty50-market-intelligence` if available |

Streamlit will read dependencies from `projects/Nifty50-Market-Intelligence/requirements.txt`. If you deploy your own copy, use the separate `.streamlit.app` URL supplied by Streamlit.

## Run locally

From the root of the profile repository:

```bash
python -m pip install -r projects/Nifty50-Market-Intelligence/requirements.txt
streamlit run projects/Nifty50-Market-Intelligence/app.py
```

## Design and correctness notes

- Original MACD: 12- and 26-session EMAs, with a 9-session signal EMA. Unlike the prototype, the app computes indicators on the *full historical series* before showing the latest six sessions.
- RSI is calculated over 14 sessions.
- The high-gap rank uses `(highest observed High over latest 252 sessions - latest Close) / highest High * 100` so a 10% gap means the last price is 10% below the trailing high. This is distinct from the original prototype's `(high - close) / close` ratio.
- Original Buy/Sell labels are **indicator regimes** (MACD above/below its signal), **not** investment recommendations or tested trade strategies.
- NSE announcements are requested only after pressing Load; external PDF links open at source instead of being automatically downloaded onto the app server.
- All sample charts are synthetic; there is no broker integration, backtested investment alpha, trading automation or price prediction claim.

## Project files

- `app.py` — interactive Streamlit dashboard and Plotly visualisations
- `engine.py` — validated OHLCV data, synthetic fixture and quantitative indicators
- `data_sources.py` — isolated Yahoo Finance and NSE RSS loaders
- `test_engine.py` — formula, history, reproducibility, RSS and validation regression tests
- `requirements.txt` — Streamlit Community Cloud dependencies

## Tests

```bash
cd projects/Nifty50-Market-Intelligence
python -m unittest discover -p "test_*.py" -v
```

GitHub Actions also checks Python compilation, tests and the Streamlit initial render using a local, synthetic dataset.

**Disclaimer:** Portfolio research and educational visualisation only. Not financial advice.

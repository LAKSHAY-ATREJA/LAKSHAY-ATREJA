# Nifty 50 Market Intelligence

An independent financial-data analytics project exploring equity screening and market signals across the Nifty 50 universe. The original Python/Streamlit prototype covers MACD-based trend signals, the distance between a stock's last traded price and its 52-week high, and listed-company announcements from an RSS feed.

## Project status

**Research prototype under redevelopment.** The original scripts are being consolidated into a reproducible analytics pipeline and an interactive Streamlit dashboard. This folder is an initial project page; the new dashboard and public live demo are **not yet available**.

## Focus

- **Market screening:** compare historical trends across Nifty 50 constituents.
- **MACD:** inspect 12-period and 26-period exponential moving averages and the 9-period signal line.
- **52-week high analysis:** compare recent closing prices with the highest price over the previous year.
- **Company announcements:** parse financial-market RSS headlines and provide links to source announcements.
- **Visual analytics:** a dashboard is planned for market breadth, individual ticker studies, filters and charts.

The legacy scripts use Python, pandas, yfinance, requests, Beautiful Soup and Streamlit. They require refactoring for resilient market data access and reproducible results before being presented as a finished application.

## Responsible use

Experimental financial-data visualisation only, not trading advice or validated buy/sell predictions. Market data may be delayed and data feeds can change. No live trading, brokerage connection or performance guarantees are claimed.

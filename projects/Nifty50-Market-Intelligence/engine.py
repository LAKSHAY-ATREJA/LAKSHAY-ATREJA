"""Nifty 50 Market Intelligence: deterministic analytics and screeners.

The original research prototype used a static 50-ticker NSE watchlist, MACD
(12, 26, 9), distance from a one-year high and NSE RSS announcements.
This module preserves those concepts but computes indicators from the *full*
history rather than truncating history before calculating the EMA.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Snapshot from the original scripts, not a claim of current index membership.
ORIGINAL_NIFTY_WATCHLIST = (
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS",
    "BAJAJ-AUTO.NS", "BAJAJFINSV.NS", "BAJFINANCE.NS", "BHARTIARTL.NS", "BPCL.NS",
    "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS",
    "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
    "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "INDUSINDBK.NS",
    "INFY.NS", "ITC.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LT.NS",
    "M&M.NS", "MARUTI.NS", "NESTLEIND.NS", "NTPC.NS", "ONGC.NS",
    "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS",
    "SHRIRAMFIN.NS", "SUNPHARMA.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS",
    "TECHM.NS", "TITAN.NS", "ULTRACEMCO.NS", "UPL.NS", "WIPRO.NS"
)
OHLCV = ["Open", "High", "Low", "Close", "Volume"]


def normalise_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Validate single-symbol daily OHLCV with no silent fabrication."""
    if df.empty:
        raise ValueError("Market series is empty.")
    frame = df.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        if len(set(frame.columns.get_level_values(-1))) == 1:
            frame.columns = frame.columns.get_level_values(0)
        elif len(set(frame.columns.get_level_values(0))) == 1:
            frame.columns = frame.columns.get_level_values(-1)
        else:
            raise ValueError("Specify one ticker before normalising OHLCV.")
    if not set(OHLCV).issubset(frame.columns):
        raise ValueError("OHLCV requires Open, High, Low, Close, Volume.")
    if isinstance(frame.index, pd.DatetimeIndex):
        out = frame[OHLCV].copy()
        out.index = pd.to_datetime(out.index, utc=True).tz_localize(None).normalize()
    elif "Date" in frame.columns:
        out = frame.set_index(pd.to_datetime(frame["Date"], utc=True).dt.tz_localize(None).dt.normalize())[OHLCV].copy()
    else:
        raise ValueError("A DatetimeIndex or Date column is required.")
    for key in OHLCV:
        out[key] = pd.to_numeric(out[key], errors="coerce")
    out = out.replace([np.inf, -np.inf], np.nan).dropna()
    out = out[~out.index.duplicated(keep="last")].sort_index()
    out = out[(out[["Open", "High", "Low", "Close"]] > 0).all(axis=1)]
    if len(out) < 40:
        raise ValueError("At least 40 valid daily price observations are required.")
    return out


def with_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    """MACD 12/26/9 and 14-day RSI, using historical prices only."""
    x = normalise_prices(frame)
    close = x["Close"]
    x["EMA12"] = close.ewm(span=12, adjust=False).mean()
    x["EMA26"] = close.ewm(span=26, adjust=False).mean()
    x["MACD"] = x["EMA12"] - x["EMA26"]
    x["SignalLine"] = x["MACD"].ewm(span=9, adjust=False).mean()
    x["Histogram"] = x["MACD"] - x["SignalLine"]
    delta = close.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    average_gain = gains.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    average_loss = losses.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = average_gain / average_loss.replace(0, np.nan)
    x["RSI14"] = (100 - 100/(1 + rs)).clip(0,100)
    x.loc[(average_loss == 0) & (average_gain > 0), "RSI14"] = 100.0
    x.loc[(average_loss == 0) & (average_gain == 0), "RSI14"] = 50.0
    x["DailyReturn"] = close.pct_change()
    x["MA20"] = close.rolling(20).mean()
    x["MA50"] = close.rolling(50).mean()
    x["Signal"] = np.where(x["Histogram"] > 0, "Buy", np.where(x["Histogram"] < 0, "Sell", "Hold"))
    # Labels are historical indicator regimes, not trading recommendations.
    x["Crossover"] = np.where(
        (x["Histogram"] > 0) & (x["Histogram"].shift(1) <= 0), "Bullish crossover",
        np.where((x["Histogram"] < 0) & (x["Histogram"].shift(1) >= 0),
                 "Bearish crossover", "None")
    )
    return x


def demonstration_market(symbols=ORIGINAL_NIFTY_WATCHLIST, periods: int = 260) -> dict[str,pd.DataFrame]:
    """Deterministic, *synthetic* OHLCV across original 50-ticker watchlist."""
    if periods < 60:
        raise ValueError("Demo requires at least 60 sessions.")
    dates = pd.bdate_range(end="2026-10-30", periods=periods)
    generated = {}
    for pos, symbol in enumerate(symbols):
        rng = np.random.default_rng(2030 + pos * 31)
        base = 110 + (pos * 137 % 4700)
        drift = (pos % 9 - 4) * .00019 + .00028
        returns = rng.normal(drift, .009 + pos % 7 * .0015, periods)
        # A handful of visually inspectable trend changes.
        returns[112:132] += (1 if pos % 3 == 0 else -1) * .0025
        close = base * np.exp(np.cumsum(returns))
        opening = np.r_[base,close[:-1]] * (1 + rng.normal(0,.0025,periods))
        wick = rng.uniform(.003,.018,periods)
        high = np.maximum(opening,close) * (1 + wick)
        low = np.minimum(opening,close) * (1 - wick*.8)
        volume = rng.integers(50_000,1_200_000,periods)
        raw = pd.DataFrame({"Open":opening,"High":high,"Low":low,
                            "Close":close,"Volume":volume},index=dates)
        generated[symbol] = normalise_prices(raw)
    return generated


def universe_screener(history: dict[str,pd.DataFrame]) -> pd.DataFrame:
    """Compute a watchlist snapshot and high-to-close gap for each usable ticker."""
    rows = []
    for symbol, raw in sorted(history.items()):
        try:
            x = with_indicators(raw)
        except (ValueError, KeyError, TypeError):
            continue
        last = x.iloc[-1]
        year = x.tail(252)
        top = float(year["High"].max())
        bottom = float(year["Low"].min())
        last_close = float(last["Close"])
        previous = float(x["Close"].iloc[-2])
        volatility = float(x["DailyReturn"].tail(60).std() * np.sqrt(252) * 100)
        rows.append({
            "Ticker":symbol, "Last":round(last_close,2),
            "1D %":round(100*(last_close/previous-1),2),
            "52W High":round(top,2), "52W Low":round(bottom,2),
            "Below High %":round(100*(top-last_close)/top,2),
            "MACD":round(float(last["MACD"]),3),
            "SignalLine":round(float(last["SignalLine"]),3),
            "Histogram":round(float(last["Histogram"]),3),
            "Regime":str(last["Signal"]),
            "Crossover":str(last["Crossover"]),
            "RSI14":round(float(last["RSI14"]),1) if pd.notna(last["RSI14"]) else np.nan,
            "Volatility %":round(volatility,2),
            "As of":x.index[-1].date().isoformat(),
        })
    if not rows:
        return pd.DataFrame(columns=[
            "Ticker","Last","1D %","52W High","52W Low","Below High %",
            "MACD","SignalLine","Histogram","Regime","Crossover","RSI14","Volatility %","As of"
        ])
    return pd.DataFrame(rows).sort_values("Ticker").reset_index(drop=True)


def recent_signal_history(raw: pd.DataFrame, days: int = 6) -> pd.DataFrame:
    """Last N regimes *after* indicator computation over full price history."""
    x = with_indicators(raw).tail(days)
    result = x[["Close","MACD","SignalLine","Histogram","Signal","Crossover"]].copy()
    result.index.name = "Date"
    return result.reset_index()


def market_breadth(screener: pd.DataFrame) -> dict:
    if screener.empty:
        return {"count":0, "buys":0, "sells":0, "advancing":0, "declining":0, "mean_return":0.0}
    return {
        "count":len(screener),
        "buys":int((screener["Regime"]=="Buy").sum()),
        "sells":int((screener["Regime"]=="Sell").sum()),
        "advancing":int((screener["1D %"]>0).sum()),
        "declining":int((screener["1D %"]<0).sum()),
        "mean_return":float(screener["1D %"].mean()),
    }

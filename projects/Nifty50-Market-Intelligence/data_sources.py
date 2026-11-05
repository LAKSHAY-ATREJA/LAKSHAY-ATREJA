"""Live market and NSE announcement adapters. Network calls are opt-in."""
from __future__ import annotations
import re
from urllib.parse import urlparse
import pandas as pd
import requests
from bs4 import BeautifulSoup
from engine import normalise_prices

NSE_RSS = "https://nsearchives.nseindia.com/content/RSS/Online_announcements.xml?n=12341"

def live_prices(symbols: tuple[str,...]) -> tuple[dict[str,pd.DataFrame],list[str]]:
    """Fetch selected NSE watchlist tickers, tolerating partial Yahoo Finance failures."""
    import yfinance as yf
    results = {}
    warnings = []
    # Batches are kinder to a public data endpoint than sequential per-ticker calls.
    for start in range(0,len(symbols),15):
        group = list(symbols[start:start+15])
        try:
            raw = yf.download(group,period="18mo",auto_adjust=True,
                              progress=False,threads=True,group_by="ticker",
                              timeout=15)
        except Exception as exc:
            warnings.append(f"Request failed for batch {start//15+1}: {type(exc).__name__}")
            continue
        if raw is None or raw.empty:
            warnings.append(f"No prices returned for batch {start//15+1}")
            continue
        for ticker in group:
            try:
                if isinstance(raw.columns,pd.MultiIndex):
                    if ticker in raw.columns.get_level_values(0):
                        one = raw[ticker]
                    elif ticker in raw.columns.get_level_values(1):
                        one = raw.xs(ticker,axis=1,level=1)
                    else:
                        raise ValueError("Ticker omitted by provider.")
                else:
                    if len(group)!=1: raise ValueError("Provider returned an ambiguous column layout.")
                    one = raw
                results[ticker] = normalise_prices(one)
            except (ValueError,KeyError,TypeError) as exc:
                warnings.append(f"{ticker}: {str(exc)[:85]}")
    return results,warnings


def parse_nse_rss(xml: bytes,limit: int = 50) -> pd.DataFrame:
    """Parse only feed-authored titles and links. Do not auto-download PDFs."""
    if len(xml)>2_000_000:
        raise ValueError("Announcement response is too large.")
    soup=BeautifulSoup(xml,"xml")
    records=[]
    for item in soup.find_all("item")[:limit]:
        title=item.find("title")
        link=item.find("link")
        published=item.find("pubDate")
        description=item.find("description")
        title_text=title.get_text(" ",strip=True) if title else "Untitled filing"
        url=link.get_text(strip=True) if link else ""
        parsed=urlparse(url)
        # Link out only to the NSE's own source domains.
        if parsed.scheme!="https" or not (
            parsed.hostname=="nseindia.com" or
            (parsed.hostname or "").endswith(".nseindia.com")
        ):
            url=""
        summary=description.get_text(" ",strip=True)[:260] if description else ""
        matches=re.search(r"(?:dividend|Rs\.?)\s*(?:of\s*)?(?:₹|Rs\.?\s*)?([0-9]+(?:\.[0-9]+)?)",
                          summary,re.IGNORECASE)
        records.append({
            "Announcement":title_text[:210],
            "Published":published.get_text(" ",strip=True) if published else "",
            "Description":summary,
            "Dividend mention":matches.group(1) if matches else "",
            "Source URL":url,
        })
    return pd.DataFrame(records,columns=["Announcement","Published","Description","Dividend mention","Source URL"])


def load_nse_announcements()->pd.DataFrame:
    headers={"User-Agent":"Mozilla/5.0 (compatible; portfolio-analytics/1.0)",
             "Accept":"application/rss+xml, application/xml, text/xml"}
    try:
        response=requests.get(NSE_RSS,headers=headers,timeout=12)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ValueError("The NSE announcements feed could not be reached. Try again later.") from exc
    result=parse_nse_rss(response.content)
    if result.empty:
        raise ValueError("The NSE feed returned no readable announcements.")
    return result

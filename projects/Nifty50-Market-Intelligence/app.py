"""Nifty 50 Market Intelligence — interactive market analysis studio.

The default market is deterministic simulated data for recruiter-friendly demos.
All live data requests are opt-in; never blend simulated data with live quotes.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from engine import (
    ORIGINAL_NIFTY_WATCHLIST, demonstration_market, universe_screener,
    with_indicators, recent_signal_history, market_breadth
)
from data_sources import live_prices, load_nse_announcements

st.set_page_config(page_title="NIFTY / Market Intelligence", page_icon="📈",
                   layout="wide", initial_sidebar_state="expanded")

ACCENT="#5eead4"
BLUE="#61a5fa"
RED="#fb7185"
MUTED="#8ea6bd"
PAPER="#0c1424"
BG="#0a1120"

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {background: radial-gradient(ellipse at 88% 0%, rgba(34,84,107,.19),transparent 33%), #0a1120;}
[data-testid="stSidebar"] {background: #0d182b; border-right:1px solid #1c3046;}
.block-container {max-width: 1500px; padding-top: 1.7rem; padding-bottom:4.5rem;}
h1,h2,h3 {letter-spacing:-.039em; font-weight:700;}
h1 {font-size: 3.0rem !important;line-height: 1.07;}
[data-testid="stMetric"] {padding:17px 19px;background:linear-gradient(125deg,rgba(56,97,130,.17),rgba(29,55,75,.11));
border:1px solid rgba(117,163,191,.22);border-radius:14px;min-height:110px;}
[data-testid="stMetricLabel"]{color:#a8bdd0;}
[data-testid="stMetricValue"]{font-size:1.87rem;}
div[data-testid="stTabs"] button{font-weight:650;letter-spacing:-.015em;}
[data-testid="stDataFrame"]{border:1px solid #1b3046;border-radius:13px;overflow:hidden;}
[data-testid="stDownloadButton"] button {border-radius:9px;border:1px solid #236079;}
[data-testid="stButton"] button{border-radius:9px;}
.hero-kicker{color:#55cfc2;font-size:.76rem;letter-spacing:.20em;font-weight:750;}
.hero-copy{color:#b3c3d4;font-size:1.05rem;max-width:930px;line-height:1.65;margin:.55rem 0 1.18rem;}
.tag{display:inline-block;background:rgba(34,211,177,.085);border:1px solid rgba(34,211,177,.2);
border-radius:30px;padding:6px 12px;margin:0 9px 13px 0;color:#82ddcf;font-size:.78rem;}
.source-demo{font-size:.83rem;color:#fbbf24;background:rgba(245,158,11,.09);
border:1px solid rgba(245,158,11,.25);padding:11px 16px;border-radius:11px;}
.source-live{font-size:.83rem;color:#54e0bd;background:rgba(52,211,153,.09);
border:1px solid rgba(52,211,153,.25);padding:11px 16px;border-radius:11px;}
.sec-label{color:#7dabc2;font-size:.78rem;letter-spacing:.1em;text-transform:uppercase;font-weight:600;}
</style>
""",unsafe_allow_html=True)


def chart_style(fig:go.Figure,height=370):
    fig.update_layout(
        template="plotly_dark",height=height,
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#bbccdc",family="Arial"),
        margin=dict(l=5,r=10,t=15,b=25),
        xaxis=dict(showgrid=False,zeroline=False),
        yaxis=dict(gridcolor="rgba(145,164,182,.12)",zeroline=False),
        legend=dict(orientation="h",y=1.14,x=0, bgcolor="rgba(0,0,0,0)")
    )
    return fig


def price_chart(frame:pd.DataFrame):
    x=with_indicators(frame).tail(130)
    fig=make_subplots(rows=3,cols=1,shared_xaxes=True,
        row_heights=[.60,.23,.17],vertical_spacing=.055)
    fig.add_trace(go.Candlestick(x=x.index,open=x.Open,high=x.High,low=x.Low,close=x.Close,
        increasing_line_color=ACCENT,decreasing_line_color=RED,
        name="OHLC"),row=1,col=1)
    fig.add_trace(go.Scatter(x=x.index,y=x.MA20,name="MA 20",line=dict(color="#fbbf24",width=1.6)),row=1,col=1)
    fig.add_trace(go.Scatter(x=x.index,y=x.MA50,name="MA 50",line=dict(color=BLUE,width=1.6)),row=1,col=1)
    fig.add_trace(go.Bar(x=x.index,y=x.Volume,name="Volume",marker_color="#466782",
                         opacity=.8),row=2,col=1)
    hist_colors=np.where(x.Histogram>=0,ACCENT,RED)
    fig.add_trace(go.Bar(x=x.index,y=x.Histogram,marker_color=hist_colors,
                         name="MACD histogram",opacity=.8),row=3,col=1)
    fig.add_trace(go.Scatter(x=x.index,y=x.MACD,name="MACD",line=dict(color=BLUE,width=1.4)),row=3,col=1)
    fig.add_trace(go.Scatter(x=x.index,y=x.SignalLine,name="Signal",line=dict(color="#fbbf24",width=1.3)),row=3,col=1)
    chart_style(fig,610)
    fig.update_xaxes(rangeslider_visible=False,row=1,col=1)
    fig.update_yaxes(title_text="Price ₹",row=1,col=1)
    fig.update_yaxes(title_text="Volume",row=2,col=1)
    fig.update_yaxes(title_text="MACD",row=3,col=1)
    fig.update_layout(xaxis_rangeslider_visible=False)
    return fig


with st.sidebar:
    st.markdown("### MARKET / STUDIO")
    st.caption("Historical indicators · Nifty watchlist")
    source=st.radio("Data source",["Instant demo • simulated","Yahoo Finance • live prices"],
        help="The demo opens instantly. Live quotes are requested from an external provider and may be delayed, missing or rate-limited.")
    refresh=st.button("Refresh data",use_container_width=True)
    if refresh:
        st.cache_data.clear()
    st.divider()
    st.caption("Watchlist from the original project, not the current official Nifty 50 constituents list.")
    universe=st.multiselect("Watchlist coverage",ORIGINAL_NIFTY_WATCHLIST,
                            default=list(ORIGINAL_NIFTY_WATCHLIST),
                            help="Narrow the screening universe for faster live fetches.")
    if not universe:
        st.warning("Select at least one company to continue.")
        st.stop()
    st.divider()
    st.caption("Indicators: EMA 12/26, MACD 9-signal, RSI 14, distance from trailing 52-week high.")
    st.caption("Educational analytics only; never investment advice.")

@st.cache_data(show_spinner="Building reproducible sample market...",ttl=1800)
def demo_cached(symbols:tuple):
    return demonstration_market(symbols)

@st.cache_data(show_spinner="Fetching market data from Yahoo Finance...",ttl=1200)
def live_cached(symbols:tuple):
    return live_prices(symbols)

selected=tuple(universe)
warnings=[]
is_demo=source.startswith("Instant")
if is_demo:
    history=demo_cached(selected)
else:
    history,warnings=live_cached(selected)
    if not history:
        st.error("Yahoo Finance did not return usable prices. Check the connection or choose the instant demo in the sidebar.")
        if warnings: st.caption("Provider diagnostics: "+"; ".join(warnings[:4]))
        st.stop()

screener=universe_screener(history)
if screener.empty:
    st.error("No usable stocks were returned. Select different tickers.")
    st.stop()
breadth=market_breadth(screener)

st.markdown('<div class="hero-kicker">MARKET RESEARCH / INTERACTIVE TERMINAL</div>',
            unsafe_allow_html=True)
st.title("NIFTY 50  /  Market Intelligence")
st.markdown('<p class="hero-copy">From raw market data to an actionable research workspace: '
            'discover momentum changes, compare technical indicators, study price divergence '
            'and inspect exchange announcements — in one analyst-facing dashboard.</p>',
            unsafe_allow_html=True)
st.markdown('<span class="tag">Trend & momentum</span><span class="tag">52-week gap analysis</span>'
            '<span class="tag">Multi-stock screener</span><span class="tag">NSE announcements</span>',
            unsafe_allow_html=True)

if is_demo:
    st.markdown('<div class="source-demo"><b>SIMULATED DEMO</b> · 260 reproducible trading sessions. '
                'All prices and metrics below are synthetic, not real equity quotes. '
                'Switch the sidebar to Yahoo Finance to request actual historical prices.</div>',unsafe_allow_html=True)
else:
    st.markdown('<div class="source-live"><b>LIVE SOURCE SELECTED</b> · Yahoo Finance historical prices, '
                'as of the latest session returned. Prices can be delayed and constituents may have changed.</div>',
                unsafe_allow_html=True)
    if warnings:
        st.warning(f"{len(warnings)} ticker/data warnings. Partial results are shown; "
                   "view provider diagnostics in the Market Data tab.")

st.caption(f"{breadth['count']} of {len(universe)} selected tickers with usable history  ·  "
           f"Latest observation: {screener['As of'].max()}  ·  "
           "MACD regime labels are not trade recommendations.")
a,b,c,d=st.columns(4)
a.metric("Stocks analysed",f"{breadth['count']}")
b.metric("Bullish MACD regime",f"{breadth['buys']}",help="MACD exceeds its 9-period signal.")
c.metric("Advancing today",f"{breadth['advancing']}",help="Positive change versus previous close in selected data.")
d.metric("Average 1-day move",f"{breadth['mean_return']:+.2f}%")

tabs=st.tabs(["01  Market pulse","02  Momentum terminal","03  52-week opportunities",
              "04  Corporate announcements","05  Market data & exports"])

with tabs[0]:
    left,right=st.columns([1.55,1],gap="large")
    with left:
        st.subheader("Momentum landscape")
        st.caption("Each point is one stock: latest return versus RSI; size shows recent volatility.")
        fig=go.Figure()
        for regime,color in [("Buy",ACCENT),("Sell",RED),("Hold",MUTED)]:
            segment=screener[screener.Regime==regime]
            if segment.empty:continue
            fig.add_trace(go.Scatter(
                x=segment["RSI14"],y=segment["1D %"],mode="markers",
                name="MACD "+regime,
                marker=dict(size=np.clip(segment["Volatility %"].fillna(0)*.58,8,26),
                            color=color,opacity=.84,line=dict(width=.75,color="#10283b")),
                customdata=np.stack([segment["Ticker"],segment["Last"]],axis=1),
                hovertemplate="<b>%{customdata[0]}</b><br>RSI: %{x:.1f}<br>1D: %{y:+.2f}%<br>Last ₹%{customdata[1]:.2f}<extra></extra>"
            ))
        fig.add_hline(y=0,line_dash="dot",line_color="#64748b")
        fig.add_vline(x=50,line_dash="dot",line_color="#64748b")
        fig.update_xaxes(title_text="RSI (14)",range=[0,100])
        fig.update_yaxes(title_text="Change vs previous close (%)")
        st.plotly_chart(chart_style(fig,415),use_container_width=True)
    with right:
        st.subheader("Signal distribution")
        fig=go.Figure(go.Pie(
            labels=["Bullish","Bearish","Neutral"],
            values=[breadth["buys"],breadth["sells"],
                    breadth["count"]-breadth["buys"]-breadth["sells"]],
            hole=.73,marker=dict(colors=[ACCENT,RED,"#8294a7"]),
            textinfo="label+percent",sort=False))
        fig.update_layout(annotations=[dict(text=str(breadth["count"]),x=.5,y=.5,
            font=dict(size=36,color="#d4eef2"),showarrow=False)])
        st.plotly_chart(chart_style(fig,285),use_container_width=True)
        st.markdown('<div class="sec-label">Leadership / latest session</div>',unsafe_allow_html=True)
        movers=screener.nlargest(4,"1D %")[["Ticker","1D %"]]
        st.dataframe(movers,hide_index=True,use_container_width=True)
    st.divider()
    st.subheader("Research focus")
    leaders=screener.sort_values("1D %").iloc[
        np.r_[np.arange(min(5,len(screener))), np.arange(max(5,len(screener)-5),len(screener))]
    ].drop_duplicates("Ticker")
    c=["#fb7185" if x<0 else "#5eead4" for x in leaders["1D %"]]
    fig=go.Figure(go.Bar(x=leaders["1D %"],y=leaders["Ticker"],
                         orientation="h",marker_color=c,
                         hovertemplate="%{y}: %{x:+.2f}%<extra></extra>"))
    fig.update_layout(xaxis_title="Latest one-session change (%)",yaxis_title="")
    st.plotly_chart(chart_style(fig,360),use_container_width=True)

with tabs[1]:
    st.subheader("Multi-stock MACD screener")
    left,right=st.columns([1,1])
    with left:
        focus=st.selectbox("Inspect stock",sorted(history),key="focus")
    with right:
        regime_filter=st.multiselect("Filter regimes",["Buy","Sell","Hold"],
                                    default=["Buy","Sell","Hold"])
    filtered=screener[screener.Regime.isin(regime_filter)]
    st.dataframe(filtered[["Ticker","Last","1D %","MACD","SignalLine","Histogram",
                           "RSI14","Regime","Crossover"]].sort_values("Histogram",ascending=False),
                 hide_index=True,use_container_width=True)
    st.subheader(f"{focus.replace('.NS','')} / Technical chart")
    st.caption("Candlesticks, moving averages, volume and 12/26/9 MACD are calculated on the full available history.")
    st.plotly_chart(price_chart(history[focus]),use_container_width=True)
    frame=recent_signal_history(history[focus],6)
    left,right=st.columns([1,1])
    with left:
        st.markdown("**Recent six-session signal trail**")
        st.dataframe(frame[["Date","Close","MACD","SignalLine","Signal","Crossover"]],
                     hide_index=True,use_container_width=True)
    with right:
        latest=with_indicators(history[focus]).iloc[-1]
        st.markdown("**Indicator diagnostics**")
        x,y=st.columns(2)
        x.metric("RSI (14)",f"{latest['RSI14']:.1f}")
        y.metric("Histogram",f"{latest['Histogram']:+.2f}")
        st.caption("The original project classified MACD above/below its signal line as Buy/Sell. "
                   "Here, those labels are displayed as indicator regimes, not investment advice.")

with tabs[2]:
    st.subheader("Distance from 52-week highs")
    st.caption("Original high-variance idea, standardized as (rolling 252-session high − last close) / high.")
    v=screener.sort_values("Below High %",ascending=False)
    left,right=st.columns([1.45,1],gap="large")
    with left:
        best=v.head(15).iloc[::-1]
        fig=go.Figure(go.Bar(
            y=best["Ticker"],x=best["Below High %"],orientation="h",
            marker=dict(color=best["Below High %"],colorscale=[[0,"#2dd4bf"],[.55,"#61a5fa"],[1,"#a78bfa"]]),
            hovertemplate="%{y}<br>%{x:.2f}% below high<extra></extra>"))
        fig.update_layout(xaxis_title="Below trailing high (%)",yaxis_title="")
        st.plotly_chart(chart_style(fig,530),use_container_width=True)
    with right:
        st.markdown("**Top watchlist divergences**")
        st.dataframe(v.head(15)[["Ticker","Last","52W High","52W Low","Below High %","Volatility %"]],
                     hide_index=True,use_container_width=True)
        st.caption("Distance to a high is not evidence that a stock is undervalued.")
    st.download_button("Export high-gap screener",v.to_csv(index=False).encode(),
                       "nifty50_52week_gap.csv","text/csv",use_container_width=True)

with tabs[3]:
    st.subheader("NSE corporate announcements")
    st.write("Inspect public exchange announcements from the original research feed. "
             "No automated PDF downloading or scraping occurs in the background.")
    st.caption("News is requested only when you click Load. Feed access is subject to NSE availability.")
    if "nse_announcements" not in st.session_state:
        st.session_state.nse_announcements=None
    if st.button("Load current NSE announcements",type="primary"):
        try:
            with st.spinner("Reading exchange feed..."):
                st.session_state.nse_announcements=load_nse_announcements()
        except ValueError as exc:
            st.session_state.nse_announcements=None
            st.error(str(exc))
    feed=st.session_state.nse_announcements
    if feed is not None and not feed.empty:
        st.metric("Exchange announcements",len(feed))
        q=st.text_input("Filter announcements by company or keyword",placeholder="Dividend, results, company name")
        matched=feed[feed.Announcement.str.contains(q,case=False,regex=False,na=False)] if q else feed
        st.dataframe(matched,hide_index=True,use_container_width=True,
                     column_config={"Source URL":st.column_config.LinkColumn("NSE filing")})
        st.download_button("Export filings CSV",matched.to_csv(index=False).encode(),
                           "nse_announcements.csv","text/csv")
    else:
        st.info("Press the Load button to view current announcements. This demo does not fabricate live headlines.")
    st.markdown("Source: [NSE corporate announcements feed](https://nsearchives.nseindia.com/content/RSS/Online_announcements.xml?n=12341).")

with tabs[4]:
    st.subheader("Dataset integrity & reproducibility")
    data_rows=[]
    for ticker,frame in sorted(history.items()):
        data_rows.append({"Ticker":ticker,"Sessions":len(frame),
                          "Start":str(frame.index.min().date()),
                          "Latest":str(frame.index.max().date()),
                          "Last price":round(float(frame.Close.iloc[-1]),2)})
    st.dataframe(pd.DataFrame(data_rows),hide_index=True,use_container_width=True)
    st.markdown("**Coverage diagnostics**")
    st.json({"source":"SYNTHETIC SAMPLE" if is_demo else "YAHOO FINANCE",
             "selected_tickers":len(selected),
             "usable_tickers":len(history),
             "latest_market_session":str(screener["As of"].max()),
             "notes":"Original watchlist snapshot; current official index membership is not verified."})
    if warnings:
        with st.expander("Live provider warnings"):
            for warning in warnings[:100]:
                st.write(warning)
    st.download_button("Download full technical screener (CSV)",
                       screener.to_csv(index=False).encode(),
                       "nifty50_market_screener.csv","text/csv",type="primary")
    st.caption("No brokerage connectivity, automated trading or prediction performance is claimed.")

"""Regression tests for analytical core and provider parsing (no live network)."""
import unittest
import numpy as np
import pandas as pd
from engine import (
    ORIGINAL_NIFTY_WATCHLIST, demonstration_market, normalise_prices,
    with_indicators, universe_screener, recent_signal_history, market_breadth
)
from data_sources import parse_nse_rss

class MarketAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = demonstration_market(ORIGINAL_NIFTY_WATCHLIST[:6])

    def test_50_original_symbols(self):
        self.assertEqual(len(ORIGINAL_NIFTY_WATCHLIST),50)
        self.assertEqual(len(set(ORIGINAL_NIFTY_WATCHLIST)),50)

    def test_demo_reproducible(self):
        a=demonstration_market(("INFY.NS",))["INFY.NS"]
        b=demonstration_market(("INFY.NS",))["INFY.NS"]
        self.assertTrue(a.equals(b))

    def test_ohlc_price_bounds(self):
        x=self.history["ADANIENT.NS"]
        self.assertTrue((x.High>=x[["Open","Close"]].max(axis=1)).all())
        self.assertTrue((x.Low<=x[["Open","Close"]].min(axis=1)).all())

    def test_full_history_before_last_six_sessions(self):
        sample=self.history["ADANIENT.NS"]
        recent=recent_signal_history(sample,6)
        entire=with_indicators(sample)
        self.assertEqual(len(recent),6)
        self.assertAlmostEqual(recent.MACD.iloc[0],entire.MACD.iloc[-6],places=7)
        self.assertEqual(recent.Signal.iloc[-1],entire.Signal.iloc[-1])

    def test_macd_formula(self):
        x=with_indicators(self.history["ADANIENT.NS"])
        self.assertTrue(np.allclose(x.MACD,x.EMA12-x.EMA26))
        self.assertTrue(np.allclose(x.Histogram,x.MACD-x.SignalLine))
        self.assertTrue(x.RSI14.dropna().between(0,100).all())

    def test_single_ticker_screener(self):
        x=universe_screener({"INFY.NS":self.history["ADANIENT.NS"]})
        self.assertEqual(len(x),1)
        self.assertGreaterEqual(x["Below High %"].iloc[0],0)
        self.assertLessEqual(x["Below High %"].iloc[0],100)
        self.assertIn(x["Regime"].iloc[0],("Buy","Sell","Hold"))

    def test_breadth_counts(self):
        x=universe_screener(self.history)
        b=market_breadth(x)
        self.assertEqual(b["count"],6)
        self.assertEqual(b["buys"]+b["sells"],6)

    def test_rejects_incomplete_history(self):
        short=self.history["ADANIENT.NS"].head(10)
        with self.assertRaises(ValueError):
            normalise_prices(short)

    def test_sanitises_rss_links(self):
        xml=b"""<rss><channel><item><title>Example announcement</title>
        <pubDate>Thu, 01 Jan 2026 09:00:00 GMT</pubDate>
        <link>https://nsearchives.nseindia.com/content/example.pdf</link>
        <description>Final dividend of Rs. 4.00</description></item>
        <item><title>External source</title><link>https://example.com/redirect</link></item>
        </channel></rss>"""
        frame=parse_nse_rss(xml)
        self.assertEqual(len(frame),2)
        self.assertTrue(frame.iloc[0]["Source URL"].startswith("https://nsearchives."))
        self.assertEqual(frame.iloc[1]["Source URL"],"")

if __name__=="__main__":
    unittest.main()

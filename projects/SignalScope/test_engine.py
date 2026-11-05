import unittest
import numpy as np
import pandas as pd
from engine import (demo_data, parse_telemetry, score_telemetry, group_incidents,
                    forecast_next_day, score_against_truth, export_report)

class SignalScopeAdvancedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw, cls.quality = parse_telemetry(demo_data())
        cls.scored = score_telemetry(cls.raw, 72, 3.5)

    def test_demo_is_reproducible(self):
        self.assertTrue(demo_data().equals(demo_data()))

    def test_multiple_signals_present(self):
        self.assertEqual(self.quality["services"], 4)
        self.assertEqual(self.quality["metrics"], 3)
        self.assertTrue(self.quality["has_truth_labels"])

    def test_planted_incidents_are_detected(self):
        self.assertGreater(int(self.scored["alert"].sum()), 5)
        counts = group_incidents(self.scored)
        self.assertGreater(len(counts), 0)
        self.assertTrue(counts["risk_score"].between(0,100).all())

    def test_strictly_causal_scores(self):
        key = self.raw[(self.raw.service=="Gateway")&(self.raw.metric=="latency_ms")].copy()
        first = score_telemetry(key, 48, 3.5)
        altered = key.copy()
        altered.loc[altered.index[-1], "value"] = 999999
        second = score_telemetry(altered, 48, 3.5)
        np.testing.assert_allclose(first["robust_score"].iloc[:-1], second["robust_score"].iloc[:-1], equal_nan=True)

    def test_upload_validation(self):
        with self.assertRaises(ValueError):
            parse_telemetry(b"date,value\n2026-01-01,5")

    def test_duplicate_aggregation_and_gap_tracking(self):
        data = pd.DataFrame([
            ("2026-01-01T00:00:00Z","x","calls",2),
            ("2026-01-01T00:05:00Z","x","calls",4),
            ("2026-01-01T02:00:00Z","x","calls",8),
        ], columns=["timestamp","service","metric","value"])
        parsed, quality = parse_telemetry(data)
        self.assertEqual(quality["duplicate_rows_aggregated"], 1)
        self.assertEqual(quality["missing_hourly_intervals"], 1)
        self.assertEqual(parsed.value.iloc[0], 3)

    def test_forecast_has_intervals(self):
        f = forecast_next_day(self.raw, "Payments", "latency_ms")
        self.assertEqual(len(f), 24)
        self.assertTrue((f.lower_80 <= f.forecast).all())
        self.assertTrue((f.forecast <= f.upper_80).all())

    def test_truth_backtest(self):
        metrics = score_against_truth(self.scored)
        self.assertIsNotNone(metrics)
        self.assertGreater(metrics["true_positives"], 0)
        self.assertGreaterEqual(metrics["f1"], 0)
        self.assertLessEqual(metrics["f1"], 1)

    def test_export_evidence(self):
        import json
        reports = group_incidents(self.scored)
        r = json.loads(export_report(reports, self.quality, {"window": 72}))
        self.assertEqual(len(r["incidents"]), len(reports))
        self.assertEqual(r["configuration"]["window"], 72)

if __name__ == "__main__":
    unittest.main()

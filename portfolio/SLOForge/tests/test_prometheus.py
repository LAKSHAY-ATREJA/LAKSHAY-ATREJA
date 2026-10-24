from pathlib import Path

import yaml

RULES_PATH = Path(__file__).parents[1] / "prometheus" / "slo-rules.yml"


def test_prometheus_rules_have_two_window_pairs():
    document = yaml.safe_load(RULES_PATH.read_text())
    rules = document["groups"][0]["rules"]
    records = {rule["record"]: rule["expr"] for rule in rules if "record" in rule}
    alerts = {rule["alert"]: rule for rule in rules if "alert" in rule}

    assert set(records) == {
        "slo:http_requests:error_ratio_rate5m",
        "slo:http_requests:error_ratio_rate30m",
        "slo:http_requests:error_ratio_rate1h",
        "slo:http_requests:error_ratio_rate6h",
    }
    assert set(alerts) == {"SLOFastBurn", "SLOSlowBurn"}
    assert "14.4 * 0.001" in alerts["SLOFastBurn"]["expr"]
    assert "6 * 0.001" in alerts["SLOSlowBurn"]["expr"]
    assert " and " in alerts["SLOFastBurn"]["expr"]
    assert " and " in alerts["SLOSlowBurn"]["expr"]


def test_recording_rules_avoid_zero_denominator():
    document = yaml.safe_load(RULES_PATH.read_text())
    rules = document["groups"][0]["rules"]
    expressions = [rule["expr"] for rule in rules if "record" in rule]

    assert all("clamp_min" in expression for expression in expressions)

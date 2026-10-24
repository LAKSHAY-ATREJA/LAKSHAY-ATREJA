import pytest

from sloforge.slo import SLO, AlertWindows, Window


def windows(
    *,
    fast_short: Window,
    fast_long: Window,
    slow_short: Window,
    slow_long: Window,
) -> AlertWindows:
    return AlertWindows(fast_short, fast_long, slow_short, slow_long)


def test_budget_burn_and_evidence():
    slo = SLO(0.999)
    sample = Window(good=9995, total=10000)

    assert slo.availability(sample) == 0.9995
    assert slo.error_ratio(sample) == 0.0005
    assert slo.burn_rate(sample) == pytest.approx(0.5)
    assert slo.remaining_budget(sample) == pytest.approx(0.5)
    assert slo.evidence(sample)["bad"] == 5


def test_fast_pair_requires_both_windows():
    slo = SLO(0.99)
    decision = slo.multiwindow_alert(
        windows(
            fast_short=Window(80, 100),
            fast_long=Window(99, 100),
            slow_short=Window(100, 100),
            slow_long=Window(1000, 1000),
        )
    )

    assert decision["page"] is False
    assert decision["reasons"] == []


def test_fast_or_slow_pair_can_page():
    slo = SLO(0.99)
    fast = Window(80, 100)
    healthy = Window(100, 100)
    fast_decision = slo.multiwindow_alert(
        windows(
            fast_short=fast,
            fast_long=fast,
            slow_short=healthy,
            slow_long=healthy,
        )
    )
    slow_decision = slo.multiwindow_alert(
        windows(
            fast_short=healthy,
            fast_long=healthy,
            slow_short=Window(90, 100),
            slow_long=Window(900, 1000),
        )
    )

    assert fast_decision["reasons"] == ["fast_burn"]
    assert slow_decision["reasons"] == ["slow_burn"]


def test_zero_traffic_is_healthy_and_preserves_budget():
    slo = SLO(0.999)
    empty = Window(0, 0)

    assert slo.availability(empty) == 1.0
    assert slo.error_ratio(empty) == 0.0
    assert slo.burn_rate(empty) == 0.0
    assert slo.remaining_budget(empty) == 1.0


@pytest.mark.parametrize(
    "factory",
    [
        lambda: Window(-1, 0),
        lambda: Window(2, 1),
        lambda: SLO(0),
        lambda: SLO(1),
    ],
)
def test_invalid_domains_are_rejected(factory):
    with pytest.raises(ValueError):
        factory()


def test_invalid_threshold_is_rejected():
    healthy = Window(100, 100)
    with pytest.raises(ValueError):
        SLO(0.99).multiwindow_alert(
            windows(
                fast_short=healthy,
                fast_long=healthy,
                slow_short=healthy,
                slow_long=healthy,
            ),
            fast_threshold=0,
        )

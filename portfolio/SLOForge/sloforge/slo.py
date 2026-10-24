from __future__ import annotations

from dataclasses import dataclass

COMPARISON_TOLERANCE = 1e-12


@dataclass(frozen=True)
class Window:
    good: int
    total: int

    def __post_init__(self) -> None:
        if self.total < 0 or self.good < 0 or self.good > self.total:
            raise ValueError("counts require 0 <= good <= total")

    @property
    def bad(self) -> int:
        return self.total - self.good


@dataclass(frozen=True)
class AlertWindows:
    fast_short: Window
    fast_long: Window
    slow_short: Window
    slow_long: Window


class SLO:
    def __init__(self, target: float):
        if not 0 < target < 1:
            raise ValueError("target must be between 0 and 1")
        self.target = target

    @property
    def error_budget(self) -> float:
        return 1 - self.target

    def availability(self, window: Window) -> float:
        return 1.0 if window.total == 0 else window.good / window.total

    def error_ratio(self, window: Window) -> float:
        return 0.0 if window.total == 0 else window.bad / window.total

    def burn_rate(self, window: Window) -> float:
        return self.error_ratio(window) / self.error_budget

    def remaining_budget(self, window: Window) -> float:
        if window.total == 0:
            return 1.0
        remaining = max(0.0, 1 - self.burn_rate(window))
        return 0.0 if remaining < COMPARISON_TOLERANCE else remaining

    def evidence(self, window: Window) -> dict[str, int | float]:
        return {
            "good": window.good,
            "bad": window.bad,
            "total": window.total,
            "availability": round(self.availability(window), 12),
            "error_ratio": round(self.error_ratio(window), 12),
            "burn_rate": round(self.burn_rate(window), 12),
        }

    def multiwindow_alert(
        self,
        windows: AlertWindows,
        *,
        fast_threshold: float = 14.4,
        slow_threshold: float = 6.0,
    ) -> dict[str, object]:
        if fast_threshold <= 0 or slow_threshold <= 0:
            raise ValueError("burn-rate thresholds must be positive")

        evidence = {
            name: self.evidence(window)
            for name, window in (
                ("fast_short", windows.fast_short),
                ("fast_long", windows.fast_long),
                ("slow_short", windows.slow_short),
                ("slow_long", windows.slow_long),
            )
        }
        fast_burn = all(
            evidence[name]["burn_rate"] + COMPARISON_TOLERANCE >= fast_threshold
            for name in ("fast_short", "fast_long")
        )
        slow_burn = all(
            evidence[name]["burn_rate"] + COMPARISON_TOLERANCE >= slow_threshold
            for name in ("slow_short", "slow_long")
        )
        reasons = [
            reason
            for reason, matched in (
                ("fast_burn", fast_burn),
                ("slow_burn", slow_burn),
            )
            if matched
        ]
        return {
            "page": bool(reasons),
            "reasons": reasons,
            "thresholds": {"fast": fast_threshold, "slow": slow_threshold},
            "windows": evidence,
            "remaining_error_budget": self.remaining_budget(windows.slow_long),
        }

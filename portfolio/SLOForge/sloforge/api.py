from fastapi import FastAPI
from pydantic import BaseModel, Field, model_validator

from .slo import SLO, AlertWindows, Window

app = FastAPI(title="SLOForge", version="1.0.0")


class WindowInput(BaseModel):
    good: int = Field(ge=0)
    total: int = Field(ge=0)

    @model_validator(mode="after")
    def valid_counts(self) -> "WindowInput":
        if self.good > self.total:
            raise ValueError("good requests cannot exceed total requests")
        return self

    def domain(self) -> Window:
        return Window(good=self.good, total=self.total)


class EvaluationInput(BaseModel):
    target: float = Field(gt=0, lt=1)
    fast_short: WindowInput
    fast_long: WindowInput
    slow_short: WindowInput
    slow_long: WindowInput
    fast_threshold: float = Field(default=14.4, gt=0, le=1000)
    slow_threshold: float = Field(default=6.0, gt=0, le=1000)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "sloforge"}


@app.post("/v1/evaluate")
def evaluate(body: EvaluationInput) -> dict[str, object]:
    slo = SLO(body.target)
    windows = AlertWindows(
        fast_short=body.fast_short.domain(),
        fast_long=body.fast_long.domain(),
        slow_short=body.slow_short.domain(),
        slow_long=body.slow_long.domain(),
    )
    return {
        "target": body.target,
        "allowed_error_ratio": round(slo.error_budget, 12),
        **slo.multiwindow_alert(
            windows,
            fast_threshold=body.fast_threshold,
            slow_threshold=body.slow_threshold,
        ),
    }

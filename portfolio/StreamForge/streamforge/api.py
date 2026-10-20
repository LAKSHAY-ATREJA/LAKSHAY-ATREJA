from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

from .engine import Event, StreamEngine

app = FastAPI(title="StreamForge", version="1.0.0")
engine = StreamEngine()


class Input(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    id: str = Field(min_length=1, max_length=200)
    key: str = Field(min_length=1, max_length=200)
    value: float
    ts: float


@app.post("/v1/events")
def ingest(b: Input):
    return engine.ingest(Event(**b.model_dump()))


@app.get("/health")
def health():
    return {"status": "ok"}

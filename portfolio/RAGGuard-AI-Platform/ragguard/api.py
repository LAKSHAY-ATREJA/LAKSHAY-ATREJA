from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .eval import citation_coverage, grounded_token_ratio
from .generator import from_environment
from .guardrails import inspect_prompt
from .retrieval import Document, HybridIndex

app = FastAPI(title="RAGGuard", version="1.0.0")
index = HybridIndex(
    [
        Document(
            "arch",
            "RAG systems retrieve relevant context before generation. "
            "Evaluation should measure grounding and retrieval quality.",
        ),
        Document(
            "ops",
            "Production AI needs tracing, latency monitoring, cost controls "
            "and guardrails against prompt injection.",
        ),
        Document(
            "cloud",
            "Containerised AI APIs can run behind cloud load balancers "
            "and autoscaling infrastructure.",
        ),
    ]
)


class Query(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/query")
def query(q: Query):
    flags = inspect_prompt(q.question)
    if flags:
        raise HTTPException(400, {"blocked": True, "flags": flags})
    docs = index.search(q.question, 3)
    generation = from_environment().generate(q.question, docs)
    return {
        "answer": generation.text,
        "model": generation.model,
        "sources": [d.id for d in docs],
        "guardrail_flags": flags,
        "evaluation": {
            "citation_coverage": citation_coverage(generation.text, [d.id for d in docs]),
            "grounded_token_ratio": grounded_token_ratio(generation.text, [d.text for d in docs]),
        },
    }

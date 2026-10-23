from fastapi import FastAPI, HTTPException, Query

from .search import Doc, SearchIndex, tokenise

DEFAULT_DOCUMENTS = (
    Doc(
        "1",
        "Kubernetes autoscaling",
        "Horizontal Pod Autoscaler scales workloads using CPU and custom metrics.",
    ),
    Doc(
        "2",
        "RAG evaluation",
        "Evaluate retrieval, grounding, relevance and citation quality for AI systems.",
    ),
    Doc(
        "3",
        "Kafka streams",
        "Event-time processing must handle late and duplicated events.",
    ),
    Doc(
        "4",
        "PostgreSQL hybrid search",
        "Combine full-text search with pgvector rankings using reciprocal-rank fusion.",
    ),
)


def create_app(documents: tuple[Doc, ...] = DEFAULT_DOCUMENTS) -> FastAPI:
    app = FastAPI(title="SearchGrid", version="1.0.0")
    index = SearchIndex(documents)

    @app.get("/v1/search")
    def search(
        q: str = Query(min_length=1, max_length=200),
        k: int = Query(default=5, ge=1, le=20),
    ) -> list[dict[str, object]]:
        if not tokenise(q):
            raise HTTPException(
                status_code=422, detail="q must contain a word or number"
            )
        return [hit.as_dict() for hit in index.search(q, k)]

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "documents": len(index.docs)}

    return app


app = create_app()

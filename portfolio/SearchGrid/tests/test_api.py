from fastapi.testclient import TestClient

from searchgrid.api import app

client = TestClient(app)


def test_health_reports_loaded_document_count():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "documents": 4}


def test_search_returns_rank_evidence():
    response = client.get("/v1/search", params={"q": "Kubernetes autoscaling", "k": 1})
    assert response.status_code == 200
    result = response.json()[0]
    assert result["id"] == "1"
    assert result["lexical_rank"] == 1
    assert result["vector_rank"] == 1
    assert result["rrf_score"] > 0


def test_query_validation_rejects_empty_symbol_only_and_invalid_limit():
    assert client.get("/v1/search", params={"q": ""}).status_code == 422
    assert client.get("/v1/search", params={"q": "---"}).status_code == 422
    assert client.get("/v1/search", params={"q": "test", "k": 0}).status_code == 422

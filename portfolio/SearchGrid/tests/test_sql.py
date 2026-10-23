from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_schema_declares_full_text_and_vector_indexes():
    schema = (ROOT / "db" / "schema.sql").read_text()

    assert "CREATE EXTENSION IF NOT EXISTS vector" in schema
    assert "USING gin(search_tsv)" in schema
    assert "USING hnsw (embedding vector_cosine_ops)" in schema


def test_hybrid_query_uses_bounded_rankings_and_rrf():
    query = (ROOT / "db" / "hybrid_search.sql").read_text()

    assert "websearch_to_tsquery('english', $1)" in query
    assert "embedding <=> $2" in query
    assert "FULL OUTER JOIN semantic" in query
    assert "1.0 / (60 +" in query
    assert "LIMIT $3" in query

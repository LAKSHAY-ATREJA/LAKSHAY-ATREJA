from math import isclose, sqrt

import pytest

from searchgrid.search import Doc, SearchIndex, tokenise


@pytest.fixture
def index() -> SearchIndex:
    return SearchIndex(
        [
            Doc("a", "Containers", "Kubernetes Docker pods autoscaling"),
            Doc("b", "Search", "Embeddings vector retrieval ranking"),
            Doc("c", "Streaming", "Kafka event time windows"),
        ]
    )


def test_tokenise_normalizes_words_and_numbers():
    assert tokenise("RRF + PGVector 2026!") == ["rrf", "pgvector", "2026"]


def test_bm25_lexical_ranking(index: SearchIndex):
    ranking = index.lexical("kubernetes autoscaling")
    assert ranking[0] == 0
    assert len(ranking) == 1


def test_hash_vector_is_deterministic_and_normalized(index: SearchIndex):
    first = index.hash_vector("semantic vector search")
    second = index.hash_vector("semantic vector search")
    assert first == second
    assert isclose(sqrt(sum(value * value for value in first)), 1.0)


def test_hybrid_retrieval_exposes_both_rank_signals(index: SearchIndex):
    hit = index.search("vector retrieval", 1)[0]
    assert hit.document.id == "b"
    assert hit.lexical_rank == 1
    assert hit.vector_rank == 1
    assert hit.rrf_score > 0


def test_empty_and_invalid_index_behaviour():
    assert SearchIndex([]).search("test") == []
    assert SearchIndex([Doc("a", "one", "two")]).search("   ") == []
    with pytest.raises(ValueError, match="unique"):
        SearchIndex([Doc("duplicate", "one", ""), Doc("duplicate", "two", "")])
    with pytest.raises(ValueError, match="positive"):
        SearchIndex([]).search("query", 0)

from __future__ import annotations

import hashlib
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from math import log, sqrt

TOKEN_RE = re.compile(r"[a-z0-9]+")
RRF_K = 60


def tokenise(value: str) -> list[str]:
    """Return normalized ASCII word/number tokens."""
    return TOKEN_RE.findall(value.lower())


@dataclass(frozen=True, slots=True)
class Doc:
    id: str
    title: str
    text: str


@dataclass(frozen=True, slots=True)
class SearchHit:
    document: Doc
    rrf_score: float
    lexical_rank: int | None
    vector_rank: int | None

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.document.id,
            "title": self.document.title,
            "text": self.document.text,
            "rrf_score": round(self.rrf_score, 8),
            "lexical_rank": self.lexical_rank,
            "vector_rank": self.vector_rank,
        }


class SearchIndex:
    """In-memory BM25/hash-vector index fused with reciprocal-rank fusion."""

    def __init__(self, docs: Iterable[Doc], *, vector_dimensions: int = 128):
        if vector_dimensions < 8:
            raise ValueError("vector_dimensions must be at least 8")
        self.docs = tuple(docs)
        identifiers = [doc.id for doc in self.docs]
        if any(not identifier for identifier in identifiers):
            raise ValueError("document ids must not be empty")
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("document ids must be unique")

        self.vector_dimensions = vector_dimensions
        self.tokens = tuple(tokenise(f"{doc.title} {doc.text}") for doc in self.docs)
        self.document_frequency = Counter(
            token for tokens in self.tokens for token in set(tokens)
        )
        self.average_length = (
            sum(len(tokens) for tokens in self.tokens) / len(self.tokens)
            if self.tokens
            else 0.0
        )
        self.vectors = tuple(
            self.hash_vector(f"{doc.title} {doc.text}") for doc in self.docs
        )

    def lexical(self, query: str) -> list[int]:
        query_tokens = tokenise(query)
        if not query_tokens or not self.docs:
            return []

        query_frequency = Counter(query_tokens)
        scores: list[tuple[float, str, int]] = []
        k1 = 1.2
        b = 0.75
        for position, tokens in enumerate(self.tokens):
            term_frequency = Counter(tokens)
            score = 0.0
            for token, query_count in query_frequency.items():
                frequency = term_frequency[token]
                if not frequency:
                    continue
                document_frequency = self.document_frequency[token]
                inverse_document_frequency = log(
                    1
                    + (len(self.docs) - document_frequency + 0.5)
                    / (document_frequency + 0.5)
                )
                length_ratio = (
                    len(tokens) / self.average_length if self.average_length else 0
                )
                denominator = frequency + k1 * (1 - b + b * length_ratio)
                score += (
                    query_count
                    * inverse_document_frequency
                    * (frequency * (k1 + 1) / denominator)
                )
            if score > 0:
                scores.append((score, self.docs[position].id, position))
        scores.sort(key=lambda item: (-item[0], item[1]))
        return [position for _, _, position in scores]

    def hash_vector(self, value: str) -> tuple[float, ...]:
        vector = [0.0] * self.vector_dimensions
        for token in tokenise(value):
            digest = hashlib.blake2s(token.encode(), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.vector_dimensions
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[bucket] += sign
        magnitude = sqrt(sum(component * component for component in vector))
        if magnitude == 0:
            return tuple(vector)
        return tuple(component / magnitude for component in vector)

    def vector(self, query: str) -> list[int]:
        query_vector = self.hash_vector(query)
        if not any(query_vector):
            return []
        scores: list[tuple[float, str, int]] = []
        for position, document_vector in enumerate(self.vectors):
            similarity = sum(
                query_component * document_component
                for query_component, document_component in zip(
                    query_vector, document_vector, strict=True
                )
            )
            if similarity > 0:
                scores.append((similarity, self.docs[position].id, position))
        scores.sort(key=lambda item: (-item[0], item[1]))
        return [position for _, _, position in scores]

    def search(self, query: str, limit: int = 5) -> list[SearchHit]:
        if limit < 1:
            raise ValueError("limit must be positive")
        if not tokenise(query):
            return []

        lexical_ranking = self.lexical(query)
        vector_ranking = self.vector(query)
        scores: Counter[int] = Counter()
        lexical_ranks: dict[int, int] = {}
        vector_ranks: dict[int, int] = {}

        for rank, position in enumerate(lexical_ranking, start=1):
            lexical_ranks[position] = rank
            scores[position] += 1 / (RRF_K + rank)
        for rank, position in enumerate(vector_ranking, start=1):
            vector_ranks[position] = rank
            scores[position] += 1 / (RRF_K + rank)

        ordered = sorted(
            scores,
            key=lambda position: (-scores[position], self.docs[position].id),
        )
        return [
            SearchHit(
                document=self.docs[position],
                rrf_score=scores[position],
                lexical_rank=lexical_ranks.get(position),
                vector_rank=vector_ranks.get(position),
            )
            for position in ordered[:limit]
        ]

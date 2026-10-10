from __future__ import annotations

import hashlib
import re
from collections import Counter
from dataclasses import dataclass
from math import log, sqrt

TOKEN = re.compile(r"[a-z0-9]+")


def toks(s):
    return TOKEN.findall(s.lower())


@dataclass(frozen=True)
class Document:
    id: str
    text: str
    source: str = "local"


class HybridIndex:
    def __init__(self, docs: list[Document]):
        self.docs = docs
        self.tokens = [toks(d.text) for d in docs]
        self.df = Counter(t for ts in self.tokens for t in set(ts))
        self.avg = sum(map(len, self.tokens)) / max(1, len(self.tokens))

    def _bm25(self, q, idx):
        score = 0.0
        tf = Counter(self.tokens[idx])
        dl = len(self.tokens[idx])
        n = len(self.docs)
        for t in q:
            if not tf[t]:
                continue
            idf = log(1 + (n - self.df[t] + 0.5) / (self.df[t] + 0.5))
            score += idf * (tf[t] * 2.2) / (tf[t] + 1.2 * (0.25 + 0.75 * dl / max(self.avg, 1)))
        return score

    @staticmethod
    def _vec(text, dim=64):
        v = [0.0] * dim
        for t in toks(text):
            h = int(hashlib.sha256(t.encode()).hexdigest()[:8], 16)
            v[h % dim] += 1 if (h >> 8) & 1 else -1
        norm = sqrt(sum(x * x for x in v)) or 1
        return [x / norm for x in v]

    def search(self, query, k=4):
        q = toks(query)
        qv = self._vec(query)
        rows = []
        for i, d in enumerate(self.docs):
            dv = self._vec(d.text)
            cos = sum(a * b for a, b in zip(qv, dv))
            rows.append((0.65 * self._bm25(q, i) + 0.35 * cos, d))
        return [d for _, d in sorted(rows, key=lambda x: x[0], reverse=True)[:k]]

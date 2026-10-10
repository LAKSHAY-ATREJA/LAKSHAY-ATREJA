from __future__ import annotations

import os
from dataclasses import dataclass

import httpx

from .retrieval import Document


@dataclass
class GenerationResult:
    text: str
    model: str


class Generator:
    def generate(self, question: str, docs: list[Document]) -> GenerationResult:
        raise NotImplementedError


class EvidenceGenerator(Generator):
    """Offline fallback that preserves citations and keeps the pipeline testable."""

    def generate(self, question: str, docs: list[Document]) -> GenerationResult:
        text = "Evidence retrieved: " + " ".join(f"[{d.id}] {d.text}" for d in docs)
        return GenerationResult(text=text, model="evidence-only")


class CompatibleChatGenerator(Generator):
    """Calls any chat-completions-compatible HTTP endpoint configured at runtime."""

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def generate(self, question: str, docs: list[Document]) -> GenerationResult:
        context = "\n\n".join(f"[{d.id}] {d.text}" for d in docs)
        prompt = (
            "Answer only from the supplied evidence. "
            "Cite source ids in square brackets.\n\n"
            f"Evidence:\n{context}\n\nQuestion: {question}"
        )
        with httpx.Client(timeout=20) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                },
            )
            response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"]
        return GenerationResult(text=text, model=self.model)


def from_environment() -> Generator:
    base = os.getenv("LLM_API_BASE")
    key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL")
    if base and key and model:
        return CompatibleChatGenerator(base, key, model)
    return EvidenceGenerator()

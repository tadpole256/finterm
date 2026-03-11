from __future__ import annotations

import math
import re
from collections import Counter
from typing import Protocol

TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9_]+")


class RetrievalProvider(Protocol):
    def model_name(self) -> str: ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class MockEmbeddingRetrievalProvider(RetrievalProvider):
    def __init__(self, dim: int = 64) -> None:
        self.dim = dim

    def model_name(self) -> str:
        return "mock-hash-embed-v1"

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0 for _ in range(self.dim)]
            tokens = self._tokenize(text)
            if not tokens:
                vectors.append(vector)
                continue

            counts = Counter(tokens)
            token_count = float(sum(counts.values()))
            for token, count in counts.items():
                index = hash(token) % self.dim
                vector[index] += float(count) / token_count

            norm = math.sqrt(sum(value * value for value in vector))
            if norm > 0:
                vector = [value / norm for value in vector]
            vectors.append(vector)
        return vectors

    def _tokenize(self, text: str) -> list[str]:
        return [token.lower() for token in TOKEN_PATTERN.findall(text) if len(token) > 2]


def retrieval_provider_from_name(name: str) -> RetrievalProvider:
    normalized = name.lower().strip()
    if normalized in {"mock", "mock_embed", "mock_embedding", "embed"}:
        return MockEmbeddingRetrievalProvider()
    raise ValueError(f"Unsupported retrieval provider '{name}'")

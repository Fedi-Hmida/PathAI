import math

from app.rag.retriever import normalize_tokens


class DeterministicEmbeddingProvider:
    def __init__(self, dimension: int = 16) -> None:
        if dimension < 4:
            raise ValueError("Embedding dimension must be at least 4.")
        self.dimension = dimension

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0 for _ in range(self.dimension)]
        for token in normalize_tokens(text):
            bucket = sum(ord(char) for char in token) % self.dimension
            vector[bucket] += 1.0
        return _normalize(vector)


def _normalize(vector: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [value / magnitude for value in vector]

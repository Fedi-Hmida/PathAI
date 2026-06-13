import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class VectorSearchResult:
    resource_id: str
    score: float
    metadata: dict[str, str] = field(default_factory=dict)


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._vectors: dict[str, list[float]] = {}
        self._metadata: dict[str, dict[str, str]] = {}

    def upsert(
        self,
        resource_id: str,
        vector: list[float],
        metadata: dict[str, str] | None = None,
    ) -> None:
        self._vectors[resource_id] = vector.copy()
        self._metadata[resource_id] = dict(metadata or {})

    def query(self, vector: list[float], top_k: int = 3) -> list[VectorSearchResult]:
        scored = [
            VectorSearchResult(
                resource_id=resource_id,
                score=_cosine_similarity(vector, stored_vector),
                metadata=self._metadata.get(resource_id, {}),
            )
            for resource_id, stored_vector in self._vectors.items()
        ]
        return sorted(scored, key=lambda result: result.score, reverse=True)[:top_k]

    def count(self) -> int:
        return len(self._vectors)


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(
        left_value * right_value for left_value, right_value in zip(left, right, strict=True)
    )
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)

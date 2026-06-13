import re
from collections.abc import Iterable

from app.models.common import AccessType, DifficultyLevel
from app.rag.constants import (
    FOUNDATIONAL_FALLBACK_SCORE,
    MIN_RESOURCE_MATCH_SCORE,
    RetrievalSource,
)
from app.rag.schemas import (
    ResourceCandidate,
    ResourceCatalogItem,
    ResourceMatchExplanation,
    ResourceRetrievalRequest,
    ResourceRetrievalResult,
)

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "in",
    "of",
    "on",
    "the",
    "to",
    "with",
}

DIFFICULTY_ORDER: dict[DifficultyLevel, int] = {
    "beginner": 0,
    "intermediate": 1,
    "advanced": 2,
}


class ResourceRetriever:
    def __init__(self, catalog_items: list[ResourceCatalogItem]) -> None:
        self.catalog_items = catalog_items

    def retrieve(self, request: ResourceRetrievalRequest) -> ResourceRetrievalResult:
        candidates = [
            candidate
            for candidate in (self._score_item(item, request) for item in self.catalog_items)
            if candidate.match_score >= MIN_RESOURCE_MATCH_SCORE
        ]
        if not candidates and request.include_foundational_fallback:
            candidates = self._foundational_fallback(request)

        ordered = sorted(
            candidates,
            key=lambda candidate: (
                candidate.match_score,
                candidate.quality_score,
                candidate.resource.title.lower(),
            ),
            reverse=True,
        )[: request.top_k]
        warnings = []
        if not ordered:
            warnings.append(f"No curated resources matched topic '{request.topic}'.")
        elif len(ordered) < request.top_k:
            warnings.append(
                f"Only {len(ordered)} curated resource(s) matched topic '{request.topic}'."
            )
        return ResourceRetrievalResult(request=request, candidates=ordered, warnings=warnings)

    def _score_item(
        self,
        item: ResourceCatalogItem,
        request: ResourceRetrievalRequest,
    ) -> ResourceCandidate:
        topic_score, topic_overlap = _topic_score(
            [request.topic],
            [item.title, *item.topics, *item.subtopics],
        )
        subtopic_score, subtopic_overlap = _topic_score(
            request.subtopics,
            [item.title, *item.topics, *item.subtopics],
        )
        difficulty_score = _difficulty_score(request.difficulty, item.difficulty)
        access_score = _access_score(item.access)
        foundational_score = 1.0 if item.foundational else 0.0
        token_fallback_score = _token_overlap_score(
            normalize_tokens(" ".join([request.topic, request.goal or "", *request.subtopics])),
            normalize_tokens(" ".join([item.title, *item.topics, *item.subtopics])),
        )
        if topic_score == 0 and subtopic_score == 0 and token_fallback_score == 0:
            score = 0.0
        else:
            score = (
                topic_score * 0.34
                + subtopic_score * 0.16
                + token_fallback_score * 0.16
                + difficulty_score * 0.14
                + item.quality_score * 0.14
                + access_score * 0.04
                + foundational_score * 0.02
            )
        retrieval_source: RetrievalSource = "catalog_match" if topic_score > 0 else "token_overlap"
        explanation = ResourceMatchExplanation(
            topic_overlap=topic_overlap,
            subtopic_overlap=subtopic_overlap,
            difficulty_fit=_difficulty_fit_label(request.difficulty, item.difficulty),
            quality_signal=f"Quality score {item.quality_score:.2f}.",
            access_signal=f"Access is {item.access}.",
            notes=_candidate_notes(item, topic_score, subtopic_score, token_fallback_score),
        )
        return ResourceCandidate(
            resource=item,
            match_score=round(min(score, 1.0), 4),
            topic_score=round(topic_score, 4),
            subtopic_score=round(subtopic_score, 4),
            difficulty_score=round(difficulty_score, 4),
            quality_score=item.quality_score,
            retrieval_source=retrieval_source,
            why_this=_why_this(item, request, explanation),
            explanation=explanation,
        )

    def _foundational_fallback(
        self,
        request: ResourceRetrievalRequest,
    ) -> list[ResourceCandidate]:
        foundational_items = [
            item for item in self.catalog_items if item.foundational or item.quality_score >= 0.85
        ]
        fallback: list[ResourceCandidate] = []
        for item in foundational_items:
            explanation = ResourceMatchExplanation(
                topic_overlap=[],
                subtopic_overlap=[],
                difficulty_fit=_difficulty_fit_label(request.difficulty, item.difficulty),
                quality_signal=f"Quality score {item.quality_score:.2f}.",
                access_signal=f"Access is {item.access}.",
                notes=[
                    "Used as a curated foundational fallback because no direct match was found."
                ],
            )
            fallback.append(
                ResourceCandidate(
                    resource=item,
                    match_score=FOUNDATIONAL_FALLBACK_SCORE,
                    topic_score=0.0,
                    subtopic_score=0.0,
                    difficulty_score=_difficulty_score(request.difficulty, item.difficulty),
                    quality_score=item.quality_score,
                    retrieval_source="foundational_fallback",
                    why_this=(
                        "Curated foundational fallback while the resource catalog lacks "
                        f"a direct match for {request.topic}."
                    ),
                    explanation=explanation,
                )
            )
        return fallback


def normalize_tokens(text: str) -> list[str]:
    return [
        token
        for token in TOKEN_PATTERN.findall(text.lower())
        if token not in STOPWORDS and len(token) > 1
    ]


def _topic_score(queries: Iterable[str], resource_fields: Iterable[str]) -> tuple[float, list[str]]:
    query_tokens = set(normalize_tokens(" ".join(queries)))
    resource_tokens = set(normalize_tokens(" ".join(resource_fields)))
    if not query_tokens or not resource_tokens:
        return 0.0, []
    overlap = sorted(query_tokens & resource_tokens)
    if not overlap:
        return 0.0, []
    return min(len(overlap) / len(query_tokens), 1.0), overlap


def _token_overlap_score(query_tokens: list[str], resource_tokens: list[str]) -> float:
    query_set = set(query_tokens)
    resource_set = set(resource_tokens)
    if not query_set or not resource_set:
        return 0.0
    return min(len(query_set & resource_set) / len(query_set), 1.0)


def _difficulty_score(target: DifficultyLevel, actual: DifficultyLevel) -> float:
    distance = abs(DIFFICULTY_ORDER[target] - DIFFICULTY_ORDER[actual])
    if distance == 0:
        return 1.0
    if distance == 1:
        return 0.65
    return 0.35


def _access_score(access: AccessType) -> float:
    if access == "free":
        return 1.0
    if access == "institutional":
        return 0.75
    if access == "paid":
        return 0.25
    return 0.35


def _difficulty_fit_label(target: DifficultyLevel, actual: DifficultyLevel) -> str:
    if target == actual:
        return f"Exact difficulty match: {actual}."
    return f"Requested {target}, resource is {actual}."


def _candidate_notes(
    item: ResourceCatalogItem,
    topic_score: float,
    subtopic_score: float,
    token_fallback_score: float,
) -> list[str]:
    notes: list[str] = []
    if topic_score > 0:
        notes.append("Matched the requested topic.")
    if subtopic_score > 0:
        notes.append("Matched one or more requested subtopics.")
    if token_fallback_score > 0 and topic_score == 0:
        notes.append("Matched through token-overlap fallback.")
    if item.foundational:
        notes.append("Marked as foundational by the curation workflow.")
    return notes or ["Candidate came from deterministic catalog scoring."]


def _why_this(
    item: ResourceCatalogItem,
    request: ResourceRetrievalRequest,
    explanation: ResourceMatchExplanation,
) -> str:
    strongest = "topic"
    if explanation.subtopic_overlap:
        strongest = "subtopic"
    elif item.foundational:
        strongest = "foundational"
    return (
        f"Selected for {request.topic} based on {strongest} fit, "
        f"{explanation.difficulty_fit.lower()} and {explanation.quality_signal.lower()}"
    )

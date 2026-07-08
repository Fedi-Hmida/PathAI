from __future__ import annotations

from collections.abc import Iterable

from app.schemas.assessment import ConceptEvidence
from app.schemas.enums import ConceptClassification
from app.schemas.knowledge_map import (
    ConceptMasteryDTO,
    KnowledgeMapAgentInput,
    KnowledgeMapAgentOutput,
)

MISSING_CURRICULUM_READY_CONCEPTS: tuple[str, ...] = (
    "reranking",
    "production_rag_failures",
)

_LABELS: dict[str, str] = {
    "api_basics": "API basics",
    "chunking": "Chunking strategy",
    "embeddings": "Embeddings",
    "hallucination_reduction": "Hallucination reduction",
    "machine_learning_basics": "Machine learning basics",
    "production_rag_failures": "Production RAG failure modes",
    "python_basics": "Python basics",
    "rag_fundamentals": "RAG fundamentals",
    "reranking": "Reranking",
    "retrieval": "Retrieval",
    "retrieval_evaluation": "Retrieval evaluation",
    "vector_search": "Vector search",
}

_RECOMMENDED_ACTIONS: dict[str, str] = {
    "chunking": "Practice chunk-size and overlap tradeoffs with toy documents.",
    "embeddings": "Review how embeddings represent semantic similarity.",
    "production_rag_failures": "Add examples of production RAG failure modes.",
    "reranking": "Introduce reranking after retrieval metrics are stable.",
    "retrieval_evaluation": "Add retrieval metrics practice before project integration.",
    "vector_search": "Review vector similarity and index behavior.",
}

_PREREQUISITES: dict[str, list[str]] = {
    "reranking": ["retrieval_evaluation"],
    "retrieval_evaluation": ["retrieval"],
    "vector_search": ["embeddings"],
}


def build_knowledge_map_output(payload: KnowledgeMapAgentInput) -> KnowledgeMapAgentOutput:
    evidence_by_concept = {item.concept_id: item for item in payload.concept_evidence}
    concept_ids = _ordered_concepts(payload, evidence_by_concept)
    concepts = [
        _concept_mastery(concept_id, evidence_by_concept.get(concept_id))
        for concept_id in concept_ids
    ]

    strong = _concept_ids_for(concepts, ConceptClassification.STRONG)
    developing = _concept_ids_for(concepts, ConceptClassification.DEVELOPING)
    weak = _concept_ids_for(concepts, ConceptClassification.WEAK)
    missing = _concept_ids_for(concepts, ConceptClassification.MISSING)

    return KnowledgeMapAgentOutput(
        concepts=concepts,
        strong_concepts=strong,
        developing_concepts=developing,
        weak_concepts=weak,
        missing_concepts=missing,
        confidence=_knowledge_map_confidence(payload.concept_evidence, concepts),
        summary=_summary(strong=strong, developing=developing, weak=weak, missing=missing),
    )


def _concept_mastery(
    concept_id: str,
    evidence: ConceptEvidence | None,
) -> ConceptMasteryDTO:
    score = round(evidence.score, 2) if evidence else 0.0
    classification = _classification_for_score(score, has_evidence=evidence is not None)
    return ConceptMasteryDTO(
        concept_id=concept_id,
        label=_LABELS.get(concept_id, concept_id.replace("_", " ").title()),
        mastery_score=score,
        classification=classification,
        evidence=evidence.evidence if evidence else ["No direct diagnostic evidence yet."],
        prerequisites=_PREREQUISITES.get(concept_id, []),
        recommended_action=_recommended_action(concept_id, classification),
        confidence=0.82 if evidence else 0.45,
    )


def _classification_for_score(
    score: float,
    *,
    has_evidence: bool,
) -> ConceptClassification:
    if not has_evidence or score < 0.20:
        return ConceptClassification.MISSING
    if score < 0.45:
        return ConceptClassification.WEAK
    if score < 0.75:
        return ConceptClassification.DEVELOPING
    return ConceptClassification.STRONG


def _ordered_concepts(
    payload: KnowledgeMapAgentInput,
    evidence_by_concept: dict[str, ConceptEvidence],
) -> list[str]:
    from_answers = [
        concept_id
        for answer in payload.assessment_answers
        for concept_id in answer.question.target_concepts
    ]
    concepts = [
        *evidence_by_concept,
        *from_answers,
        *MISSING_CURRICULUM_READY_CONCEPTS,
    ]
    preferred_order = [
        "rag_fundamentals",
        "retrieval",
        "api_basics",
        "python_basics",
        "machine_learning_basics",
        "chunking",
        "embeddings",
        "retrieval_evaluation",
        "vector_search",
        "hallucination_reduction",
        "production_rag_failures",
        "reranking",
    ]
    unique = _unique(concepts)
    return [
        *[concept for concept in preferred_order if concept in unique],
        *sorted(concept for concept in unique if concept not in preferred_order),
    ]


def _concept_ids_for(
    concepts: list[ConceptMasteryDTO],
    classification: ConceptClassification,
) -> list[str]:
    return [
        concept.concept_id
        for concept in concepts
        if concept.classification == classification
    ]


def _knowledge_map_confidence(
    evidence: list[ConceptEvidence],
    concepts: list[ConceptMasteryDTO],
) -> float:
    if not concepts:
        return 0.0
    evidence_coverage = len(evidence) / len(concepts)
    confidence = 0.45 + (0.35 * evidence_coverage)
    return round(min(0.86, confidence), 2)


def _summary(
    *,
    strong: list[str],
    developing: list[str],
    weak: list[str],
    missing: list[str],
) -> str:
    return (
        "Recommended level: intermediate. "
        f"Strengths: {_format_concepts(strong)}. "
        f"Developing areas: {_format_concepts(developing)}. "
        f"Weak concepts: {_format_concepts(weak)}. "
        f"Missing concepts: {_format_concepts(missing)}."
    )


def _recommended_action(
    concept_id: str,
    classification: ConceptClassification,
) -> str | None:
    if classification in {ConceptClassification.WEAK, ConceptClassification.MISSING}:
        return _RECOMMENDED_ACTIONS.get(
            concept_id,
            "Add targeted practice before moving deeper.",
        )
    if classification == ConceptClassification.DEVELOPING:
        return _RECOMMENDED_ACTIONS.get(concept_id)
    return None


def _format_concepts(concepts: list[str]) -> str:
    if not concepts:
        return "none"
    labels = [_LABELS.get(concept, concept.replace("_", " ")) for concept in concepts]
    return ", ".join(labels)


def _unique(values: Iterable[str]) -> list[str]:
    unique_values: list[str] = []
    for value in values:
        if value not in unique_values:
            unique_values.append(value)
    return unique_values

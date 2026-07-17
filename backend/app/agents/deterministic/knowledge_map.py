from __future__ import annotations

from collections.abc import Iterable

from app.schemas.assessment import ConceptEvidence
from app.schemas.enums import ConceptClassification
from app.schemas.knowledge_map import (
    ConceptMasteryDTO,
    KnowledgeMapAgentInput,
    KnowledgeMapAgentOutput,
)


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
        label=concept_id.replace("_", " ").title(),
        mastery_score=score,
        classification=classification,
        evidence=evidence.evidence if evidence else ["No direct diagnostic evidence yet."],
        prerequisites=[],
        recommended_action=_recommended_action(classification),
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
    concepts = [*evidence_by_concept, *from_answers]
    return _unique(concepts)


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


def _recommended_action(classification: ConceptClassification) -> str | None:
    if classification in {ConceptClassification.WEAK, ConceptClassification.MISSING}:
        return "Add targeted practice before moving deeper."
    return None


def _format_concepts(concepts: list[str]) -> str:
    if not concepts:
        return "none"
    labels = [concept.replace("_", " ") for concept in concepts]
    return ", ".join(labels)


def _unique(values: Iterable[str]) -> list[str]:
    unique_values: list[str] = []
    for value in values:
        if value not in unique_values:
            unique_values.append(value)
    return unique_values

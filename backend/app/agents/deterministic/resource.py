from __future__ import annotations

from dataclasses import dataclass

from app.fixtures import canonical_demo as demo
from app.schemas.curriculum import CurriculumTopicDTO
from app.schemas.resource import (
    ResourceAgentInput,
    ResourceAgentOutput,
    ResourceAttachmentDTO,
    ResourceCoverageSummary,
    ResourceDTO,
)


@dataclass(frozen=True, slots=True)
class ResourceMatch:
    resource: ResourceDTO
    relevance_score: float
    concept_overlap: int
    tag_overlap: int


def build_resource_output(payload: ResourceAgentInput) -> ResourceAgentOutput:
    attachments: list[ResourceAttachmentDTO] = []
    warnings: list[str] = []
    for topic in _curriculum_topics(payload):
        matches = _rank_resources(topic, payload)
        if not matches:
            warnings.append(f"No deterministic resource match for topic {topic.topic_id}.")
            continue
        for rank, match in enumerate(matches[: payload.max_resources_per_topic], start=1):
            attachments.append(_attachment_for_match(payload, topic, match, rank))

    return ResourceAgentOutput(
        attachments=attachments,
        coverage_summary=_coverage_summary(payload, attachments),
        warnings=warnings + _diversity_warnings(attachments),
    )


def _rank_resources(
    topic: CurriculumTopicDTO,
    payload: ResourceAgentInput,
) -> list[ResourceMatch]:
    matches = [
        match
        for resource in payload.corpus_resources
        if (match := _match_resource(topic, resource, payload)) is not None
    ]
    return sorted(
        matches,
        key=lambda item: (
            -item.relevance_score,
            item.resource.resource_type.value,
            item.resource.resource_id,
        ),
    )


def _match_resource(
    topic: CurriculumTopicDTO,
    resource: ResourceDTO,
    payload: ResourceAgentInput,
) -> ResourceMatch | None:
    topic_concepts = set(topic.concept_ids)
    resource_concepts = set(resource.concept_ids)
    concept_overlap = len(topic_concepts & resource_concepts)
    tag_overlap = len(_topic_terms(topic) & set(resource.topic_tags))
    if concept_overlap == 0 and tag_overlap == 0:
        return None

    weak_or_missing = set(payload.knowledge_map.weak_concepts) | set(
        payload.knowledge_map.missing_concepts,
    )
    weak_bonus = 0.07 if resource_concepts & weak_or_missing else 0.0
    difficulty_bonus = 0.04 if resource.difficulty == topic.difficulty else 0.0
    relevance = (
        0.48
        + (0.17 * concept_overlap)
        + (0.04 * tag_overlap)
        + (0.16 * resource.quality_score)
        + weak_bonus
        + difficulty_bonus
    )
    return ResourceMatch(
        resource=resource,
        relevance_score=round(min(0.98, relevance), 2),
        concept_overlap=concept_overlap,
        tag_overlap=tag_overlap,
    )


def _attachment_for_match(
    payload: ResourceAgentInput,
    topic: CurriculumTopicDTO,
    match: ResourceMatch,
    rank: int,
) -> ResourceAttachmentDTO:
    resource = match.resource
    return ResourceAttachmentDTO(
        attachment_id=_attachment_id(topic, resource),
        goal_id=payload.curriculum.goal_id,
        curriculum_id=payload.curriculum.curriculum_id,
        topic_id=topic.topic_id,
        resource_id=resource.resource_id,
        rank=rank,
        relevance_score=match.relevance_score,
        selection_reason=_selection_reason(topic, match),
        quality_score_snapshot=resource.quality_score,
        diversity_category=resource.resource_type.value,
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )


def _coverage_summary(
    payload: ResourceAgentInput,
    attachments: list[ResourceAttachmentDTO],
) -> ResourceCoverageSummary:
    topic_ids = {topic.topic_id for topic in _curriculum_topics(payload)}
    covered_topic_ids = {attachment.topic_id for attachment in attachments}
    average_relevance = (
        round(
            sum(attachment.relevance_score for attachment in attachments) / len(attachments),
            2,
        )
        if attachments
        else 0.0
    )
    diversity = _resource_type_diversity(attachments)
    return ResourceCoverageSummary(
        topics_with_resources=len(topic_ids & covered_topic_ids),
        topics_without_resources=len(topic_ids - covered_topic_ids),
        average_relevance=average_relevance,
        resource_type_diversity=diversity,
    )


def _resource_type_diversity(attachments: list[ResourceAttachmentDTO]) -> float:
    if not attachments:
        return 0.0
    categories = {
        attachment.diversity_category
        for attachment in attachments
        if attachment.diversity_category
    }
    return round(min(1.0, len(categories) / 5), 2)


def _diversity_warnings(attachments: list[ResourceAttachmentDTO]) -> list[str]:
    if _resource_type_diversity(attachments) >= 0.6:
        return []
    return ["Resource diversity is limited in the deterministic local corpus."]


def _selection_reason(topic: CurriculumTopicDTO, match: ResourceMatch) -> str:
    concepts = ", ".join(sorted(set(topic.concept_ids) & set(match.resource.concept_ids)))
    if not concepts:
        concepts = "topic tags"
    return (
        f"Selected for {topic.title} because it matches {concepts} "
        f"with deterministic relevance {match.relevance_score:.2f}."
    )


def _attachment_id(topic: CurriculumTopicDTO, resource: ResourceDTO) -> str:
    topic_token = topic.topic_id.removeprefix("topic_")
    resource_token = resource.resource_id.removeprefix("resource_")
    return f"attach_{topic_token}_{resource_token}"[:127]


def _curriculum_topics(payload: ResourceAgentInput) -> list[CurriculumTopicDTO]:
    return [
        topic
        for week in payload.curriculum.weeks
        for topic in week.topics
    ]


def _topic_terms(topic: CurriculumTopicDTO) -> set[str]:
    terms = set(topic.concept_ids)
    for value in [topic.title, topic.description]:
        terms.update(
            part.strip().lower().replace("-", "_")
            for part in value.split()
            if len(part.strip()) > 2
        )
    return terms

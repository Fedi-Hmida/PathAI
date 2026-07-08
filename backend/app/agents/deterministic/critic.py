from __future__ import annotations

from app.schemas.critic import (
    CriticAgentInput,
    CriticAgentOutput,
    CriticDimensionScores,
)
from app.schemas.curriculum import CurriculumDTO, CurriculumTopicDTO
from app.schemas.enums import CriticPassStatus
from app.schemas.resource import ResourceAttachmentDTO

MAX_DEMO_WEEK_HOURS = 7.0

PREREQUISITES: dict[str, tuple[str, ...]] = {
    "vector_search": ("embeddings",),
    "retrieval_evaluation": ("retrieval",),
    "reranking": ("retrieval_evaluation",),
    "production_rag_failures": ("hallucination_reduction",),
}


def build_critic_output(payload: CriticAgentInput) -> CriticAgentOutput:
    weak_or_missing = [
        *payload.knowledge_map.weak_concepts,
        *payload.knowledge_map.missing_concepts,
    ]
    topic_concepts = _curriculum_concepts(payload.curriculum)
    uncovered = [concept for concept in weak_or_missing if concept not in topic_concepts]
    overloaded_weeks = [
        week.week_number
        for week in payload.curriculum.weeks
        if week.estimated_hours > MAX_DEMO_WEEK_HOURS
    ]
    prerequisite_issues = _prerequisite_issues(payload.curriculum)
    diversity_score = _diversity_score(payload.resource_attachments)

    dimension_scores = CriticDimensionScores(
        coverage=_coverage_score(weak_or_missing, uncovered),
        pacing=_pacing_score(payload.curriculum, overloaded_weeks),
        resource_relevance=_resource_relevance_score(
            payload.resource_attachments,
            diversity_score,
        ),
        assessment_alignment=_assessment_alignment_score(weak_or_missing, topic_concepts),
        quiz_readiness=_quiz_readiness_score(payload.curriculum, weak_or_missing),
    )
    issues = _issues(
        uncovered=uncovered,
        overloaded_weeks=overloaded_weeks,
        prerequisite_issues=prerequisite_issues,
        diversity_score=diversity_score,
        curriculum=payload.curriculum,
        attachments=payload.resource_attachments,
    )
    overall_score = _overall_score(dimension_scores)
    return CriticAgentOutput(
        overall_score=overall_score,
        pass_status=_pass_status(overall_score, issues),
        dimension_scores=dimension_scores,
        strengths=_strengths(
            uncovered=uncovered,
            prerequisite_issues=prerequisite_issues,
            curriculum=payload.curriculum,
            attachments=payload.resource_attachments,
        ),
        issues=issues,
        revision_recommendations=_recommendations(issues),
    )


def _coverage_score(weak_or_missing: list[str], uncovered: list[str]) -> float:
    if not weak_or_missing:
        return 0.84
    covered_ratio = (len(weak_or_missing) - len(uncovered)) / len(weak_or_missing)
    return round(0.55 + (0.4 * covered_ratio), 2)


def _pacing_score(curriculum: CurriculumDTO, overloaded_weeks: list[int]) -> float:
    total_hours = sum(week.estimated_hours for week in curriculum.weeks)
    average_hours = total_hours / len(curriculum.weeks)
    overload_penalty = 0.11 * len(overloaded_weeks)
    average_penalty = max(0.0, average_hours - MAX_DEMO_WEEK_HOURS) * 0.04
    return round(max(0.35, 0.92 - overload_penalty - average_penalty), 2)


def _resource_relevance_score(
    attachments: list[ResourceAttachmentDTO],
    diversity_score: float,
) -> float:
    if not attachments:
        return 0.25
    average_relevance = sum(item.relevance_score for item in attachments) / len(attachments)
    return round(min(0.95, (average_relevance * 0.75) + (diversity_score * 0.2)), 2)


def _assessment_alignment_score(
    weak_or_missing: list[str],
    topic_concepts: set[str],
) -> float:
    if not weak_or_missing:
        return 0.84
    covered = len([concept for concept in weak_or_missing if concept in topic_concepts])
    return round(0.5 + (0.42 * (covered / len(weak_or_missing))), 2)


def _quiz_readiness_score(curriculum: CurriculumDTO, weak_or_missing: list[str]) -> float:
    topics = _topics(curriculum)
    checkpoint_count = len([topic for topic in topics if topic.assessment_checkpoint])
    practice_count = len([topic for topic in topics if topic.practice_task])
    weak_practice_count = len(
        [
            topic
            for topic in topics
            if set(topic.concept_ids) & set(weak_or_missing) and topic.practice_task
        ],
    )
    score = 0.46 + (0.08 * checkpoint_count) + (0.04 * practice_count)
    if weak_or_missing:
        score += 0.18 * (weak_practice_count / len(weak_or_missing))
    return round(min(0.92, score), 2)


def _issues(
    *,
    uncovered: list[str],
    overloaded_weeks: list[int],
    prerequisite_issues: list[str],
    diversity_score: float,
    curriculum: CurriculumDTO,
    attachments: list[ResourceAttachmentDTO],
) -> list[str]:
    issues: list[str] = []
    if uncovered:
        issues.append(f"Weak or missing concepts lack explicit topics: {_format(uncovered)}.")
    if overloaded_weeks:
        issues.append(f"Weeks exceed the deterministic workload target: {overloaded_weeks}.")
    issues.extend(prerequisite_issues)
    if diversity_score < 0.6:
        issues.append("Resource diversity is below the deterministic local-demo target.")
    if _practice_ratio(curriculum) < 0.65:
        issues.append("Theory/practice balance is weak because too few topics have practice tasks.")
    if not attachments:
        issues.append("No resource attachments are available for critic review.")
    return issues[:20]


def _strengths(
    *,
    uncovered: list[str],
    prerequisite_issues: list[str],
    curriculum: CurriculumDTO,
    attachments: list[ResourceAttachmentDTO],
) -> list[str]:
    strengths: list[str] = []
    if not uncovered:
        strengths.append("Weak and missing concepts are explicitly represented in the curriculum.")
    if not prerequisite_issues:
        strengths.append("Prerequisites appear before advanced RAG topics.")
    if _practice_ratio(curriculum) >= 0.65:
        strengths.append("Most topics include hands-on practice tasks.")
    covered_topics = {attachment.topic_id for attachment in attachments}
    topic_ids = {topic.topic_id for topic in _topics(curriculum)}
    if topic_ids and topic_ids <= covered_topics:
        strengths.append("Every curriculum topic has at least one attached resource.")
    return strengths or ["The deterministic review completed with limited positive evidence."]


def _recommendations(issues: list[str]) -> list[str]:
    recommendations: list[str] = []
    for issue in issues:
        if "concepts lack explicit topics" in issue:
            recommendations.append("Add focused topics for uncovered weak or missing concepts.")
        elif "workload" in issue:
            recommendations.append(
                "Move one topic out of overloaded weeks or reduce practice scope.",
            )
        elif "Prerequisite" in issue:
            recommendations.append("Reorder topics so prerequisites appear first.")
        elif "diversity" in issue:
            recommendations.append("Add at least three distinct resource types for the curriculum.")
        elif "Theory/practice" in issue:
            recommendations.append("Add practical tasks to theory-heavy topics.")
        elif "No resource" in issue:
            recommendations.append("Attach deterministic local corpus resources before review.")
    return recommendations[:20]


def _overall_score(scores: CriticDimensionScores) -> float:
    weighted = (
        (scores.coverage * 0.26)
        + (scores.pacing * 0.2)
        + (scores.resource_relevance * 0.22)
        + (scores.assessment_alignment * 0.2)
        + ((scores.quiz_readiness or 0.0) * 0.12)
    )
    return round(weighted, 2)


def _pass_status(overall_score: float, issues: list[str]) -> CriticPassStatus:
    if overall_score >= 0.82 and not issues:
        return CriticPassStatus.PASS
    if overall_score >= 0.72:
        return CriticPassStatus.PASS_WITH_WARNINGS
    if overall_score >= 0.55:
        return CriticPassStatus.REVISE
    return CriticPassStatus.FAILED


def _prerequisite_issues(curriculum: CurriculumDTO) -> list[str]:
    seen: set[str] = set()
    issues: list[str] = []
    for topic in sorted(_topics(curriculum), key=lambda item: item.sequence_order):
        for concept in topic.concept_ids:
            available = seen | set(topic.concept_ids)
            missing = [
                item
                for item in PREREQUISITES.get(concept, ())
                if item not in available
            ]
            if missing:
                issues.append(
                    f"Prerequisite gap before {topic.topic_id}: {_format(missing)}.",
                )
        seen.update(topic.concept_ids)
    return issues


def _curriculum_concepts(curriculum: CurriculumDTO) -> set[str]:
    return {concept for topic in _topics(curriculum) for concept in topic.concept_ids}


def _topics(curriculum: CurriculumDTO) -> list[CurriculumTopicDTO]:
    return [topic for week in curriculum.weeks for topic in week.topics]


def _diversity_score(attachments: list[ResourceAttachmentDTO]) -> float:
    if not attachments:
        return 0.0
    categories = {
        attachment.diversity_category
        for attachment in attachments
        if attachment.diversity_category
    }
    return round(min(1.0, len(categories) / 5), 2)


def _practice_ratio(curriculum: CurriculumDTO) -> float:
    topics = _topics(curriculum)
    if not topics:
        return 0.0
    practice_count = len([topic for topic in topics if topic.practice_task])
    return practice_count / len(topics)


def _format(concepts: list[str]) -> str:
    return ", ".join(concept.replace("_", " ") for concept in concepts)

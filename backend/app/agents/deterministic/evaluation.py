from __future__ import annotations

from collections.abc import Iterable

from app.schemas.adaptation import AdaptationEventDTO
from app.schemas.critic import CriticReviewDTO
from app.schemas.curriculum import CurriculumDTO, CurriculumTopicDTO
from app.schemas.enums import AdaptationStatus, DifficultyLevel, EvaluationPassStatus
from app.schemas.evaluation import (
    EvaluationAgentInput,
    EvaluationAgentOutput,
    EvaluationMetricScores,
)
from app.schemas.goal import LearningGoalDTO
from app.schemas.knowledge_map import KnowledgeMapDTO
from app.schemas.quiz import QuizAttemptDTO
from app.schemas.resource import ResourceAttachmentDTO

EVALUATION_WEIGHTS: dict[str, float] = {
    "curriculum_coverage": 0.18,
    "difficulty_alignment": 0.11,
    "pacing_balance": 0.1,
    "resource_relevance": 0.13,
    "resource_diversity": 0.08,
    "quiz_alignment": 0.13,
    "critic_coherence": 0.12,
    "workflow_completeness": 0.09,
    "adaptation_usefulness": 0.06,
}


def build_evaluation_output(payload: EvaluationAgentInput) -> EvaluationAgentOutput:
    scores = EvaluationMetricScores(
        curriculum_coverage=_curriculum_coverage(
            payload.knowledge_map,
            payload.curriculum,
        ),
        difficulty_alignment=_difficulty_alignment(payload.goal, payload.curriculum),
        pacing_balance=_pacing_balance(payload.goal, payload.curriculum),
        resource_relevance=_resource_relevance(payload.resources),
        resource_diversity=_resource_diversity(payload.resources),
        quiz_alignment=_quiz_alignment(payload.knowledge_map, payload.quiz_attempt),
        critic_coherence=_critic_coherence(payload.critic_review),
        workflow_completeness=_workflow_completeness(payload),
        adaptation_usefulness=_adaptation_usefulness(
            payload.quiz_attempt,
            payload.adaptation_event,
        ),
    )
    weighted_score = _weighted_score(scores)
    return EvaluationAgentOutput(
        metric_scores=scores,
        weighted_score=weighted_score,
        pass_status=_pass_status(weighted_score, scores),
        warnings=_warnings(payload, scores),
        recommendations=_recommendations(payload, scores),
    )


def _curriculum_coverage(
    knowledge_map: KnowledgeMapDTO,
    curriculum: CurriculumDTO,
) -> float:
    target_concepts = _unique(
        [
            *knowledge_map.weak_concepts,
            *knowledge_map.missing_concepts,
            *knowledge_map.developing_concepts,
        ],
    )
    if not target_concepts:
        return 0.84
    curriculum_concepts = _curriculum_concepts(curriculum)
    covered = len(
        [concept for concept in target_concepts if concept in curriculum_concepts],
    )
    return round(0.5 + (0.45 * (covered / len(target_concepts))), 2)


def _difficulty_alignment(goal: LearningGoalDTO, curriculum: CurriculumDTO) -> float:
    target = goal.learner_profile.difficulty_target
    topics = _topics(curriculum)
    if not topics:
        return 0.0
    exact = len([topic for topic in topics if topic.difficulty == target])
    nearby = len(
        [
            topic
            for topic in topics
            if abs(_difficulty_rank(topic.difficulty) - _difficulty_rank(target)) == 1
        ],
    )
    return round(
        min(
            1.0,
            0.48 + (0.4 * (exact / len(topics))) + (0.12 * (nearby / len(topics))),
        ),
        2,
    )


def _pacing_balance(goal: LearningGoalDTO, curriculum: CurriculumDTO) -> float:
    target_hours = goal.hours_per_week or goal.learner_profile.time_availability_hours_per_week
    if not curriculum.weeks:
        return 0.0
    penalties = [
        min(0.3, abs(week.estimated_hours - target_hours) * 0.04)
        for week in curriculum.weeks
    ]
    average_penalty = sum(penalties) / len(penalties)
    return round(max(0.35, 0.94 - average_penalty), 2)


def _resource_relevance(attachments: list[ResourceAttachmentDTO]) -> float:
    if not attachments:
        return 0.0
    return round(
        sum(attachment.relevance_score for attachment in attachments) / len(attachments),
        2,
    )


def _resource_diversity(attachments: list[ResourceAttachmentDTO]) -> float:
    if not attachments:
        return 0.0
    categories = {
        attachment.diversity_category
        for attachment in attachments
        if attachment.diversity_category
    }
    return round(min(1.0, len(categories) / 5), 2)


def _quiz_alignment(
    knowledge_map: KnowledgeMapDTO,
    quiz_attempt: QuizAttemptDTO | None,
) -> float:
    if quiz_attempt is None:
        return 0.0
    target_concepts = set(knowledge_map.weak_concepts) | set(knowledge_map.missing_concepts)
    scored_concepts = {concept_score.concept_id for concept_score in quiz_attempt.concept_scores}
    if not target_concepts:
        return 0.82
    coverage = len(target_concepts & scored_concepts) / len(target_concepts)
    signal_bonus = 0.08 if quiz_attempt.adaptation_triggered else 0.0
    return round(min(0.96, 0.5 + (0.38 * coverage) + signal_bonus), 2)


def _critic_coherence(critic_review: CriticReviewDTO | None) -> float:
    if critic_review is None:
        return 0.0
    issue_penalty = min(0.16, len(critic_review.issues) * 0.03)
    return round(max(0.0, critic_review.overall_score - issue_penalty), 2)


def _workflow_completeness(payload: EvaluationAgentInput) -> float:
    checks = [
        payload.goal is not None,
        payload.assessment is not None,
        payload.knowledge_map is not None,
        payload.curriculum is not None,
        bool(payload.resources),
        payload.critic_review is not None,
        payload.quiz_attempt is not None,
        payload.adaptation_event is not None,
    ]
    return round(sum(checks) / len(checks), 2)


def _adaptation_usefulness(
    quiz_attempt: QuizAttemptDTO | None,
    adaptation_event: AdaptationEventDTO | None,
) -> float:
    if adaptation_event is None:
        return 0.45 if quiz_attempt and quiz_attempt.adaptation_triggered else 0.78
    change_score = min(0.2, len(adaptation_event.changes) * 0.06)
    status_bonus = (
        0.08
        if adaptation_event.status
        in {AdaptationStatus.PROPOSED, AdaptationStatus.APPLIED}
        else 0.0
    )
    return round(min(0.94, 0.66 + change_score + status_bonus), 2)


def _weighted_score(scores: EvaluationMetricScores) -> float:
    payload = scores.model_dump()
    total = 0.0
    for key, weight in EVALUATION_WEIGHTS.items():
        value = payload.get(key)
        total += (value if isinstance(value, float) else 0.0) * weight
    return round(total, 2)


def _pass_status(
    weighted_score: float,
    scores: EvaluationMetricScores,
) -> EvaluationPassStatus:
    if weighted_score >= 0.82 and not _score_warnings(scores):
        return EvaluationPassStatus.PASS
    if weighted_score >= 0.7:
        return EvaluationPassStatus.PASS_WITH_WARNINGS
    return EvaluationPassStatus.FAIL


def _warnings(
    payload: EvaluationAgentInput,
    scores: EvaluationMetricScores,
) -> list[str]:
    warnings = _score_warnings(scores)
    if payload.critic_review and payload.critic_review.issues:
        warnings.append("Critic review still contains deterministic quality warnings.")
    if payload.quiz_attempt and payload.quiz_attempt.total_score < 0.65:
        warnings.append("Latest quiz score is below the adaptation threshold.")
    if (
        payload.adaptation_event
        and payload.adaptation_event.status == AdaptationStatus.PROPOSED
    ):
        warnings.append("Adaptation is proposed and has not been applied.")
    return warnings[:20]


def _score_warnings(scores: EvaluationMetricScores) -> list[str]:
    warnings: list[str] = []
    if scores.resource_diversity < 0.6:
        warnings.append("Resource diversity is below the deterministic demo target.")
    if scores.quiz_alignment < 0.75:
        warnings.append("Quiz alignment should cover more weak or missing concepts.")
    if scores.adaptation_usefulness is not None and scores.adaptation_usefulness < 0.7:
        warnings.append("Adaptation evidence is weak or missing.")
    return warnings


def _recommendations(
    payload: EvaluationAgentInput,
    scores: EvaluationMetricScores,
) -> list[str]:
    recommendations: list[str] = []
    if scores.resource_diversity < 0.6:
        recommendations.append("Add more deterministic resource types to the local corpus.")
    if scores.quiz_alignment < 0.75:
        recommendations.append("Add quiz coverage for every weak or missing concept.")
    if payload.quiz_attempt and payload.quiz_attempt.weak_concepts:
        concepts = ", ".join(
            concept.replace("_", " ") for concept in payload.quiz_attempt.weak_concepts
        )
        recommendations.append(f"Keep remediation focused on: {concepts}.")
    if payload.critic_review:
        recommendations.extend(payload.critic_review.revision_recommendations[:3])
    if not recommendations:
        recommendations.append("The deterministic run is ready for demo packaging.")
    return _unique(recommendations)[:20]


def _curriculum_concepts(curriculum: CurriculumDTO) -> set[str]:
    return {concept for topic in _topics(curriculum) for concept in topic.concept_ids}


def _topics(curriculum: CurriculumDTO) -> list[CurriculumTopicDTO]:
    return [topic for week in curriculum.weeks for topic in week.topics]


def _difficulty_rank(value: DifficultyLevel) -> int:
    return {"beginner": 1, "intermediate": 2, "advanced": 3}[value.value]


def _unique(values: Iterable[str]) -> list[str]:
    unique_values: list[str] = []
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in unique_values:
            unique_values.append(normalized)
    return unique_values

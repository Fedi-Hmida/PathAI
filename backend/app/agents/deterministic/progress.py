from __future__ import annotations

from collections.abc import Iterable

from app.fixtures import canonical_demo as demo
from app.schemas.curriculum import CurriculumDTO, CurriculumTopicDTO
from app.schemas.enums import ProgressStatus, TopicProgressStatus
from app.schemas.goal import LearningGoalDTO
from app.schemas.progress import (
    NextRecommendedAction,
    ProgressStateDTO,
    StuckEventDTO,
    TopicProgressDTO,
)
from app.schemas.quiz import QuizAttemptDTO

LOW_SCORE_THRESHOLD = 0.65
STUCK_COUNT_THRESHOLD = 2
PRIORITY_WEAK_CONCEPTS = (
    "retrieval_evaluation",
    "vector_search",
    "chunking",
    "reranking",
    "production_rag_failures",
)


def build_progress_state(
    goal: LearningGoalDTO,
    curriculum: CurriculumDTO,
    quiz_attempt: QuizAttemptDTO | None = None,
) -> ProgressStateDTO:
    topics = _topics(curriculum)
    weak_concepts = _weak_concepts(goal, topics, quiz_attempt)
    concept_scores = _concept_scores(quiz_attempt)
    topic_progress = [
        _topic_progress(topic, weak_concepts, concept_scores, quiz_attempt)
        for topic in topics
    ]
    current_topic_id = _current_topic_id(topic_progress, topics)
    stuck_events = _stuck_events(topic_progress, topics)
    return ProgressStateDTO(
        progress_state_id=demo.PROGRESS_ID,
        goal_id=goal.goal_id,
        curriculum_id=curriculum.curriculum_id,
        status=_progress_status(topic_progress, quiz_attempt, stuck_events),
        overall_completion=_overall_completion(topic_progress),
        current_topic_id=current_topic_id,
        topic_progress=topic_progress,
        weak_concepts=weak_concepts,
        stuck_events=stuck_events,
        last_activity_at=demo.NOW,
        next_recommended_action=_next_action(current_topic_id, topics, weak_concepts),
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )


def _topic_progress(
    topic: CurriculumTopicDTO,
    weak_concepts: list[str],
    concept_scores: dict[str, float],
    quiz_attempt: QuizAttemptDTO | None,
) -> TopicProgressDTO:
    topic_weak_concepts = set(topic.concept_ids) & set(weak_concepts)
    topic_scores = [
        concept_scores[concept]
        for concept in topic.concept_ids
        if concept in concept_scores
    ]
    if topic_scores:
        score = round(sum(topic_scores) / len(topic_scores), 2)
        return _progress_from_score(topic, score, topic_weak_concepts, quiz_attempt)
    if "rag_fundamentals" in topic.concept_ids:
        return TopicProgressDTO(
            topic_id=topic.topic_id,
            status=TopicProgressStatus.COMPLETED,
            completion=1.0,
            last_score=0.9,
            attempt_count=1,
            completed_at=demo.NOW,
        )
    if topic_weak_concepts:
        return TopicProgressDTO(
            topic_id=topic.topic_id,
            status=TopicProgressStatus.NEEDS_REVIEW,
            completion=0.35,
            last_score=0.45,
            attempt_count=1,
            stuck_count=1,
            notes=f"Deterministic review needed for {_format_concepts(topic_weak_concepts)}.",
        )
    return TopicProgressDTO(
        topic_id=topic.topic_id,
        status=TopicProgressStatus.NOT_STARTED,
        completion=0.0,
        attempt_count=0,
    )


def _progress_from_score(
    topic: CurriculumTopicDTO,
    score: float,
    topic_weak_concepts: set[str],
    quiz_attempt: QuizAttemptDTO | None,
) -> TopicProgressDTO:
    if score >= 0.75:
        return TopicProgressDTO(
            topic_id=topic.topic_id,
            status=TopicProgressStatus.COMPLETED,
            completion=1.0,
            last_score=score,
            attempt_count=1,
            completed_at=demo.NOW,
        )
    if score < 0.35 and topic_weak_concepts:
        return TopicProgressDTO(
            topic_id=topic.topic_id,
            status=TopicProgressStatus.STUCK,
            completion=0.2,
            last_score=score,
            attempt_count=1,
            stuck_count=STUCK_COUNT_THRESHOLD if quiz_attempt else 1,
            notes=f"Low quiz evidence for {_format_concepts(topic_weak_concepts)}.",
        )
    return TopicProgressDTO(
        topic_id=topic.topic_id,
        status=TopicProgressStatus.NEEDS_REVIEW,
        completion=max(0.35, min(0.65, score)),
        last_score=score,
        attempt_count=1,
        stuck_count=1 if topic_weak_concepts else 0,
        notes="Checkpoint evidence suggests another focused review pass.",
    )


def _weak_concepts(
    goal: LearningGoalDTO,
    topics: list[CurriculumTopicDTO],
    quiz_attempt: QuizAttemptDTO | None,
) -> list[str]:
    curriculum_concepts = {concept for topic in topics for concept in topic.concept_ids}
    weak_values: list[str] = []
    if quiz_attempt:
        weak_values.extend(quiz_attempt.weak_concepts)
    weak_values.extend(goal.learner_profile.weak_areas)
    weak_values.extend(
        concept for concept in PRIORITY_WEAK_CONCEPTS if concept in curriculum_concepts
    )
    return _unique(concept for concept in weak_values if concept in curriculum_concepts)


def _concept_scores(quiz_attempt: QuizAttemptDTO | None) -> dict[str, float]:
    if quiz_attempt is None:
        return {}
    return {
        concept_score.concept_id: concept_score.score
        for concept_score in quiz_attempt.concept_scores
    }


def _overall_completion(topic_progress: list[TopicProgressDTO]) -> float:
    if not topic_progress:
        return 0.0
    return round(
        sum(progress.completion for progress in topic_progress) / len(topic_progress),
        2,
    )


def _current_topic_id(
    topic_progress: list[TopicProgressDTO],
    topics: list[CurriculumTopicDTO],
) -> str | None:
    priority_statuses = {TopicProgressStatus.STUCK, TopicProgressStatus.NEEDS_REVIEW}
    for progress in topic_progress:
        if progress.status in priority_statuses:
            return progress.topic_id
    for progress in topic_progress:
        if progress.status == TopicProgressStatus.IN_PROGRESS:
            return progress.topic_id
    return topics[0].topic_id if topics else None


def _stuck_events(
    topic_progress: list[TopicProgressDTO],
    topics: list[CurriculumTopicDTO],
) -> list[StuckEventDTO]:
    concepts_by_topic = {topic.topic_id: topic.concept_ids for topic in topics}
    events: list[StuckEventDTO] = []
    for progress in topic_progress:
        if progress.stuck_count >= STUCK_COUNT_THRESHOLD:
            events.append(
                StuckEventDTO(
                    topic_id=progress.topic_id,
                    concept_ids=concepts_by_topic.get(progress.topic_id, []),
                    reason="Deterministic quiz evidence crossed the stuck-topic threshold.",
                    created_at=demo.NOW,
                ),
            )
    return events


def _progress_status(
    topic_progress: list[TopicProgressDTO],
    quiz_attempt: QuizAttemptDTO | None,
    stuck_events: list[StuckEventDTO],
) -> ProgressStatus:
    if topic_progress and all(
        progress.status == TopicProgressStatus.COMPLETED for progress in topic_progress
    ):
        return ProgressStatus.COMPLETED
    if stuck_events:
        return ProgressStatus.ADAPTATION_NEEDED
    if quiz_attempt and quiz_attempt.total_score < LOW_SCORE_THRESHOLD:
        return ProgressStatus.ADAPTATION_NEEDED
    return ProgressStatus.IN_PROGRESS


def _next_action(
    topic_id: str | None,
    topics: list[CurriculumTopicDTO],
    weak_concepts: list[str],
) -> NextRecommendedAction | None:
    if topic_id is None:
        return None
    topic = next((item for item in topics if item.topic_id == topic_id), None)
    label = f"Review {topic.title}" if topic else "Review current topic"
    topic_concepts = set(topic.concept_ids) if topic else set()
    relevant = [concept for concept in weak_concepts if concept in topic_concepts]
    reason = (
        f"Priority weak concepts: {_format_concepts(relevant)}."
        if relevant
        else "Continue the next deterministic checkpoint topic."
    )
    return NextRecommendedAction(topic_id=topic_id, label=label, reason=reason)


def _topics(curriculum: CurriculumDTO) -> list[CurriculumTopicDTO]:
    return [topic for week in curriculum.weeks for topic in week.topics]


def _format_concepts(concepts: Iterable[str]) -> str:
    return ", ".join(concept.replace("_", " ") for concept in _unique(concepts))


def _unique(values: Iterable[str]) -> list[str]:
    unique_values: list[str] = []
    for value in values:
        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        if normalized and normalized not in unique_values:
            unique_values.append(normalized)
    return unique_values

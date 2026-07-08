from __future__ import annotations

from collections.abc import Iterable

from app.agents.deterministic.quiz import LOW_SCORE_THRESHOLD
from app.fixtures import canonical_demo as demo
from app.schemas.adaptation import AdaptationAgentInput, AdaptationAgentOutput
from app.schemas.curriculum import CurriculumChangeDTO, CurriculumTopicDTO
from app.schemas.enums import CurriculumChangeType, DifficultyLevel
from app.schemas.progress import ProgressStateDTO
from app.schemas.quiz import QuizAttemptDTO

STUCK_COUNT_THRESHOLD = 2


def build_adaptation_output(payload: AdaptationAgentInput) -> AdaptationAgentOutput:
    weak_concepts = _weak_concepts(payload)
    trigger_reason = _trigger_reason(payload.progress_state, payload.quiz_attempt, weak_concepts)
    changes = _changes_for_concepts(payload, weak_concepts)
    return AdaptationAgentOutput(
        trigger_reason=trigger_reason,
        before_summary=_before_summary(payload.progress_state, payload.quiz_attempt),
        after_summary=_after_summary(weak_concepts),
        changes=changes,
        added_practice_topics=_practice_topics(changes),
        removed_or_deferred_topics=[],
        expected_benefit=_expected_benefit(weak_concepts),
    )


def _weak_concepts(payload: AdaptationAgentInput) -> list[str]:
    values: list[str] = []
    values.extend(payload.weak_concepts)
    if payload.quiz_attempt:
        values.extend(payload.quiz_attempt.weak_concepts)
    values.extend(payload.progress_state.weak_concepts)
    return _unique(values) or ["retrieval_evaluation"]


def _trigger_reason(
    progress_state: ProgressStateDTO,
    quiz_attempt: QuizAttemptDTO | None,
    weak_concepts: list[str],
) -> str:
    if quiz_attempt and quiz_attempt.total_score < LOW_SCORE_THRESHOLD:
        return (
            f"Quiz score {quiz_attempt.total_score:.2f} is below deterministic "
            f"threshold {LOW_SCORE_THRESHOLD:.2f}."
        )
    if progress_state.stuck_events or any(
        progress.stuck_count >= STUCK_COUNT_THRESHOLD
        for progress in progress_state.topic_progress
    ):
        return "A topic crossed the deterministic stuck-count threshold."
    return f"Weak concepts remain unresolved: {_format_concepts(weak_concepts)}."


def _changes_for_concepts(
    payload: AdaptationAgentInput,
    weak_concepts: list[str],
) -> list[CurriculumChangeDTO]:
    changes: list[CurriculumChangeDTO] = []
    for concept in weak_concepts[:3]:
        topic_id = _topic_for_concept(payload, concept)
        changes.append(
            CurriculumChangeDTO(
                change_type=_change_type_for_concept(concept),
                target_week=_week_for_topic(payload, topic_id),
                affected_topic_ids=[topic_id] if topic_id else [],
                affected_concept_ids=[concept],
                reason=_reason_for_concept(concept),
                topic_title=_topic_title_for_concept(concept),
            ),
        )
    return changes or [demo.ADAPTATION_CHANGE.model_copy(deep=True)]


def _practice_topics(changes: list[CurriculumChangeDTO]) -> list[CurriculumTopicDTO]:
    topics: list[CurriculumTopicDTO] = []
    for index, change in enumerate(changes, start=1):
        concept = (
            change.affected_concept_ids[0]
            if change.affected_concept_ids
            else "rag_fundamentals"
        )
        topics.append(
            CurriculumTopicDTO(
                topic_id=f"topic_adapt_{concept}"[:127],
                title=change.topic_title or "Focused review practice",
                description=f"Deterministic remediation practice for {concept.replace('_', ' ')}.",
                concept_ids=[concept],
                difficulty=DifficultyLevel.INTERMEDIATE,
                estimated_hours=1.5,
                learning_outcomes=[
                    f"Improve confidence with {concept.replace('_', ' ')}.",
                ],
                sequence_order=100 + index,
                practice_task=_practice_task_for_concept(concept),
                adaptation_origin=demo.ADAPTATION_ID,
            ),
        )
    return topics[:10]


def _before_summary(
    progress_state: ProgressStateDTO,
    quiz_attempt: QuizAttemptDTO | None,
) -> str:
    score = quiz_attempt.total_score if quiz_attempt else None
    if score is not None:
        return (
            f"The learner has {progress_state.overall_completion:.0%} completion "
            f"and a checkpoint score of {score:.2f}."
        )
    return f"The learner has {progress_state.overall_completion:.0%} completion."


def _after_summary(weak_concepts: list[str]) -> str:
    return (
        "The plan proposes focused remediation for "
        f"{_format_concepts(weak_concepts)} before continuing."
    )


def _expected_benefit(weak_concepts: list[str]) -> str:
    return (
        "Focused practice should improve checkpoint readiness for "
        f"{_format_concepts(weak_concepts)} without changing the active curriculum yet."
    )


def _change_type_for_concept(concept: str) -> CurriculumChangeType:
    if concept in {"retrieval_evaluation", "chunking"}:
        return CurriculumChangeType.ADD_PRACTICE_EXERCISE
    if concept in {"vector_search", "reranking"}:
        return CurriculumChangeType.ADD_REVIEW_QUIZ
    return CurriculumChangeType.ADD_RESOURCE


def _reason_for_concept(concept: str) -> str:
    return (
        f"Deterministic feedback shows {concept.replace('_', ' ')} needs another "
        "practice pass before project integration."
    )


def _topic_title_for_concept(concept: str) -> str:
    titles = {
        "retrieval_evaluation": "Practice recall and precision with toy retrieval results",
        "vector_search": "Review vector-search similarity with worked examples",
        "chunking": "Practice chunk size and overlap tradeoffs",
        "reranking": "Add a reranking checkpoint review",
        "production_rag_failures": "Review production RAG failure modes",
    }
    return titles.get(concept, f"Focused {concept.replace('_', ' ')} practice")


def _practice_task_for_concept(concept: str) -> str:
    tasks = {
        "retrieval_evaluation": "Score a tiny retrieval table with recall at k and precision at k.",
        "vector_search": "Explain why two semantically related passages should be close.",
        "chunking": "Compare two chunking layouts and choose the safer retrieval version.",
        "reranking": "Reorder three passages with a deterministic relevance rule.",
        "production_rag_failures": "Match common failures to simple mitigations.",
    }
    return tasks.get(concept, "Complete a focused deterministic review exercise.")


def _topic_for_concept(payload: AdaptationAgentInput, concept: str) -> str | None:
    for week in payload.curriculum.weeks:
        for topic in week.topics:
            if concept in topic.concept_ids:
                return topic.topic_id
    return payload.progress_state.current_topic_id


def _week_for_topic(payload: AdaptationAgentInput, topic_id: str | None) -> int | None:
    if topic_id is None:
        return None
    for week in payload.curriculum.weeks:
        if any(topic.topic_id == topic_id for topic in week.topics):
            return week.week_number
    return None


def _format_concepts(concepts: Iterable[str]) -> str:
    return ", ".join(concept.replace("_", " ") for concept in _unique(concepts))


def _unique(values: Iterable[str]) -> list[str]:
    unique_values: list[str] = []
    for value in values:
        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        if normalized and normalized not in unique_values:
            unique_values.append(normalized)
    return unique_values

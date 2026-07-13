from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from app.schemas.curriculum import (
    CurriculumAgentInput,
    CurriculumAgentOutput,
    CurriculumTopicDTO,
    CurriculumWeekDTO,
)
from app.schemas.enums import DifficultyLevel


@dataclass(frozen=True, slots=True)
class TopicBlueprint:
    topic_id: str
    title: str
    description: str
    concept_ids: tuple[str, ...]
    difficulty: DifficultyLevel
    estimated_hours: float
    learning_outcomes: tuple[str, ...]
    practice_task: str | None = None
    assessment_checkpoint: str | None = None


PREREQUISITES: dict[str, tuple[str, ...]] = {
    "vector_search": ("embeddings",),
    "retrieval_evaluation": ("retrieval",),
    "reranking": ("retrieval_evaluation",),
    "production_rag_failures": ("hallucination_reduction",),
}

TOPIC_BLUEPRINTS: dict[str, TopicBlueprint] = {
    "rag_fundamentals": TopicBlueprint(
        topic_id="topic_rag_foundations",
        title="RAG foundations and grounding",
        description="Review retrieval-augmented generation roles and grounding tradeoffs.",
        concept_ids=("rag_fundamentals", "retrieval"),
        difficulty=DifficultyLevel.BEGINNER,
        estimated_hours=2.0,
        learning_outcomes=("Explain how retrieval grounds generation.",),
        practice_task="Sketch the retriever, context builder, and generator path.",
    ),
    "chunking": TopicBlueprint(
        topic_id="topic_chunking_strategy",
        title="Chunking strategy",
        description="Compare chunk sizes, overlap, and context granularity for retrieval.",
        concept_ids=("chunking", "retrieval"),
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_hours=2.0,
        learning_outcomes=("Choose a chunking approach for project documents.",),
        practice_task="Create two chunking variants and predict retrieval tradeoffs.",
    ),
    "embeddings": TopicBlueprint(
        topic_id="topic_embeddings_review",
        title="Embeddings review",
        description="Review semantic embedding behavior before vector index design.",
        concept_ids=("embeddings",),
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_hours=2.0,
        learning_outcomes=("Explain how embeddings represent semantic similarity.",),
        practice_task="Compare two short passages and explain expected embedding similarity.",
    ),
    "vector_search": TopicBlueprint(
        topic_id="topic_vector_search",
        title="Vector search basics",
        description="Connect embeddings, similarity search, and vector index behavior.",
        concept_ids=("embeddings", "vector_search"),
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_hours=2.5,
        learning_outcomes=("Explain why embedding choice affects retrieval quality.",),
        practice_task="Trace a vector-search request from query embedding to top-k results.",
    ),
    "retrieval_evaluation": TopicBlueprint(
        topic_id="topic_retrieval_metrics",
        title="Retrieval metrics practice",
        description="Practice recall at k and precision at k with toy retrieval results.",
        concept_ids=("retrieval_evaluation",),
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_hours=3.0,
        learning_outcomes=("Compute recall at k for a small retrieval dataset.",),
        practice_task="Score a toy retrieval table using recall at k and precision at k.",
        assessment_checkpoint="Retrieval metrics checkpoint",
    ),
    "reranking": TopicBlueprint(
        topic_id="topic_reranking_intro",
        title="Reranking after retrieval",
        description="Introduce reranking as a post-retrieval quality improvement step.",
        concept_ids=("reranking", "retrieval_evaluation"),
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_hours=2.0,
        learning_outcomes=("Explain when reranking can improve retrieved context quality.",),
        practice_task="Rank three retrieved passages before and after a reranking rule.",
    ),
    "production_rag_failures": TopicBlueprint(
        topic_id="topic_production_rag",
        title="Production RAG failure modes",
        description="Identify retrieval, grounding, and hallucination failure modes.",
        concept_ids=("production_rag_failures", "hallucination_reduction"),
        difficulty=DifficultyLevel.ADVANCED,
        estimated_hours=2.5,
        learning_outcomes=("Describe two production RAG risks and mitigations.",),
        practice_task="Write a mitigation checklist for stale, irrelevant, or missing context.",
    ),
    "api_basics": TopicBlueprint(
        topic_id="topic_fastapi_rag_integration",
        title="FastAPI RAG integration",
        description="Expose a small RAG retrieval endpoint for the graduation project.",
        concept_ids=("api_basics", "system_design"),
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_hours=3.0,
        learning_outcomes=("Connect a backend endpoint to a retrieval component.",),
        practice_task="Draft the request and response DTOs for a retrieval endpoint.",
    ),
}


_RAG_WORD_PATTERN = re.compile(r"\b(rag|retrieval)\b")


def build_curriculum_output(payload: CurriculumAgentInput) -> CurriculumAgentOutput:
    is_rag_goal = _is_rag_relevant(payload)
    concepts = _prioritized_concepts(payload, is_rag_goal=is_rag_goal)
    topics = _topics_for_concepts(concepts, goal_text=payload.goal_text)
    weeks = _pack_topics(
        topics=topics,
        duration_weeks=payload.duration_weeks,
        hours_per_week=payload.hours_per_week,
        goal_text=payload.goal_text,
        is_rag_goal=is_rag_goal,
    )
    weak_or_missing = [
        *payload.knowledge_map.weak_concepts,
        *payload.knowledge_map.missing_concepts,
    ]
    return CurriculumAgentOutput(
        title=_title_for_goal(payload.goal_text),
        duration_weeks=payload.duration_weeks,
        weeks=weeks,
        assumptions=[
            "Deterministic local-demo curriculum generated from the knowledge map.",
            f"Weekly workload is planned around {payload.hours_per_week} hours per week.",
        ],
        target_outcomes=(
            [
                "Build a small RAG subsystem for the graduation project.",
                "Explain retrieval quality, vector search, and production RAG tradeoffs.",
                f"Strengthen priority concepts: {_format_concepts(weak_or_missing)}.",
            ]
            if is_rag_goal
            else [
                f"Make measurable progress on: {_bounded(payload.goal_text, 200)}.",
                f"Strengthen priority concepts: {_format_concepts(weak_or_missing)}.",
            ]
        ),
    )


def _is_rag_relevant(payload: CurriculumAgentInput) -> bool:
    knowledge_map_concepts = {
        *payload.knowledge_map.weak_concepts,
        *payload.knowledge_map.missing_concepts,
        *payload.knowledge_map.developing_concepts,
        *payload.knowledge_map.strong_concepts,
    }
    if TOPIC_BLUEPRINTS.keys() & knowledge_map_concepts:
        return True
    return bool(_RAG_WORD_PATTERN.search(payload.goal_text.lower()))


def _prioritized_concepts(payload: CurriculumAgentInput, *, is_rag_goal: bool) -> list[str]:
    # "rag_fundamentals" has no topic blueprint of its own beyond RAG
    # foundations, but its blueprint's concept_ids carry "retrieval" - the
    # only source of that concept's coverage, since "retrieval" has no
    # blueprint of its own. Only seed it for genuinely RAG-relevant goals;
    # forcing it into every curriculum was the actual bug.
    concepts: list[str] = ["rag_fundamentals"] if is_rag_goal else []
    priority_groups = (
        payload.knowledge_map.weak_concepts,
        payload.knowledge_map.missing_concepts,
        payload.knowledge_map.developing_concepts,
        payload.learner_profile.weak_areas,
        payload.knowledge_map.strong_concepts,
    )
    for group in priority_groups:
        for concept in group:
            _append_with_prerequisites(concepts, concept)
    # "api_basics" only means something here in the RAG topic blueprints
    # ("FastAPI RAG integration") - only pull it in when the learner's own
    # evidence already mentions it, not unconditionally for every goal.
    if "api_basics" in concepts:
        _append_with_prerequisites(concepts, "api_basics")
    return _unique(concepts)


def _append_with_prerequisites(concepts: list[str], concept: str) -> None:
    for prerequisite in PREREQUISITES.get(concept, ()):
        _append_with_prerequisites(concepts, prerequisite)
    if concept not in concepts:
        concepts.append(concept)


def _topics_for_concepts(
    concepts: Iterable[str],
    *,
    goal_text: str,
) -> list[CurriculumTopicDTO]:
    topics: list[CurriculumTopicDTO] = []
    seen_topic_ids: set[str] = set()
    for concept in concepts:
        blueprint = TOPIC_BLUEPRINTS.get(concept)
        if blueprint is None or blueprint.topic_id in seen_topic_ids:
            continue
        seen_topic_ids.add(blueprint.topic_id)
        topics.append(_topic_from_blueprint(blueprint, sequence_order=len(topics) + 1))
    # TOPIC_BLUEPRINTS is entirely RAG-specific - if nothing in the learner's
    # actual evidence matched any of it, inserting a RAG topic anyway would
    # be dishonest for an unrelated goal. Use a generic placeholder instead.
    return topics or [_generic_fallback_topic(goal_text)]


def _generic_fallback_topic(goal_text: str) -> CurriculumTopicDTO:
    return CurriculumTopicDTO(
        topic_id="topic_general_foundations",
        title=f"Foundations for: {_bounded(goal_text, 80)}",
        description=(
            "Deterministic placeholder topic - no matching concept blueprint exists "
            "for this goal yet. Enable the LLM curriculum agent for real, "
            "goal-specific content."
        ),
        concept_ids=["general_concepts"],
        difficulty=DifficultyLevel.BEGINNER,
        estimated_hours=2.0,
        learning_outcomes=["Review foundational concepts for this goal."],
        sequence_order=1,
    )


def _bounded(value: str, max_length: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[: max_length - 3]}..."


def _pack_topics(
    *,
    topics: list[CurriculumTopicDTO],
    duration_weeks: int,
    hours_per_week: int,
    goal_text: str,
    is_rag_goal: bool,
) -> list[CurriculumWeekDTO]:
    buckets: list[list[CurriculumTopicDTO]] = [[] for _ in range(duration_weeks)]
    week_index = 0
    for topic in topics:
        current_hours = sum(item.estimated_hours for item in buckets[week_index])
        should_advance = (
            buckets[week_index]
            and week_index < duration_weeks - 1
            and (
                current_hours + topic.estimated_hours > hours_per_week
                or len(buckets[week_index]) >= 3
            )
        )
        if should_advance:
            week_index += 1
        buckets[week_index].append(topic)

    next_sequence = len(topics) + 1
    weeks: list[CurriculumWeekDTO] = []
    for index, week_topics in enumerate(buckets, start=1):
        if not week_topics:
            week_topics = [
                _review_topic(index, next_sequence, goal_text=goal_text, is_rag_goal=is_rag_goal)
            ]
            next_sequence += 1
        weeks.append(_week_from_topics(index, week_topics))
    return weeks


def _topic_from_blueprint(
    blueprint: TopicBlueprint,
    sequence_order: int,
) -> CurriculumTopicDTO:
    return CurriculumTopicDTO(
        topic_id=blueprint.topic_id,
        title=blueprint.title,
        description=blueprint.description,
        concept_ids=list(blueprint.concept_ids),
        difficulty=blueprint.difficulty,
        estimated_hours=blueprint.estimated_hours,
        learning_outcomes=list(blueprint.learning_outcomes),
        sequence_order=sequence_order,
        practice_task=blueprint.practice_task,
        assessment_checkpoint=blueprint.assessment_checkpoint,
    )


def _review_topic(
    week_number: int,
    sequence_order: int,
    *,
    goal_text: str,
    is_rag_goal: bool,
) -> CurriculumTopicDTO:
    # Only claim the "rag_fundamentals" concept (and get real corpus-matched
    # resources/critic scoring for it) when this genuinely is a RAG goal -
    # otherwise a generic, honestly-unlabeled review topic.
    concept_id = "rag_fundamentals" if is_rag_goal else "general_concepts"
    outcome = (
        "Summarize the strongest and weakest RAG concepts so far."
        if is_rag_goal
        else f"Summarize progress so far on: {_bounded(goal_text, 120)}."
    )
    return CurriculumTopicDTO(
        topic_id=f"topic_week_{week_number}_review",
        title=f"Week {week_number} integration review",
        description="Consolidate prior concepts before moving to the next milestone.",
        concept_ids=[concept_id],
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_hours=1.5,
        learning_outcomes=[outcome],
        sequence_order=sequence_order,
        practice_task="Write a short reflection linking the week's topics to the project.",
    )


def _week_from_topics(
    week_number: int,
    topics: list[CurriculumTopicDTO],
) -> CurriculumWeekDTO:
    return CurriculumWeekDTO(
        week_id=f"week_plan_{week_number}",
        week_number=week_number,
        theme=_theme_for_week(week_number, topics),
        topics=topics,
        estimated_hours=round(sum(topic.estimated_hours for topic in topics), 2),
        learning_outcomes=_week_outcomes(topics),
        milestone=_milestone_for_week(week_number, topics),
        notes="Deterministic week plan generated from the current knowledge map.",
    )


def _theme_for_week(week_number: int, topics: list[CurriculumTopicDTO]) -> str:
    concept_ids = {concept for topic in topics for concept in topic.concept_ids}
    if {"retrieval_evaluation", "vector_search"} & concept_ids:
        return "Retrieval quality and vector search practice"
    if {"production_rag_failures", "reranking"} & concept_ids:
        return "Production retrieval quality and reliability"
    if {"api_basics", "system_design"} & concept_ids:
        return "Graduation project RAG integration"
    if week_number == 1:
        return "Foundations and prerequisite repair"
    return "Concept consolidation"


def _week_outcomes(topics: list[CurriculumTopicDTO]) -> list[str]:
    outcomes: list[str] = []
    for topic in topics:
        outcomes.extend(topic.learning_outcomes)
    return outcomes[:12]


def _milestone_for_week(week_number: int, topics: list[CurriculumTopicDTO]) -> str | None:
    if any(topic.assessment_checkpoint for topic in topics):
        return "Complete the retrieval quality checkpoint."
    if any("api_basics" in topic.concept_ids for topic in topics):
        return "Draft the graduation-project RAG integration path."
    if week_number == 1:
        return "Explain the baseline concepts and key prerequisite gaps."
    return None


def _title_for_goal(goal_text: str) -> str:
    if _RAG_WORD_PATTERN.search(goal_text.lower()):
        return "Deterministic RAG Systems Build Plan"
    return "Deterministic Learning Path Build Plan"


def _format_concepts(concepts: Iterable[str]) -> str:
    values = [concept.replace("_", " ") for concept in _unique(concepts)]
    return ", ".join(values) if values else "none"


def _unique(values: Iterable[str]) -> list[str]:
    unique_values: list[str] = []
    for value in values:
        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        if normalized and normalized not in unique_values:
            unique_values.append(normalized)
    return unique_values

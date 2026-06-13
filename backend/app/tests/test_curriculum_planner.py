from app.assessment.schemas import KnowledgeMap
from app.curriculum.planner import build_deterministic_curriculum
from app.curriculum.rules import validate_curriculum_plan
from app.curriculum.schemas import CurriculumGenerationRequest


def _knowledge_map() -> KnowledgeMap:
    return KnowledgeMap(
        strong=["Python basics"],
        weak=["Embeddings", "Evaluation"],
        missing=["Chunking", "Reranking"],
        recommended_level="beginner",
        confidence_score=0.84,
        assessment_notes=["Test map."],
    )


def test_deterministic_curriculum_respects_timeline_and_hours() -> None:
    request = CurriculumGenerationRequest(
        goal="Learn RAG systems",
        timeline_weeks=6,
        hours_per_week=8,
        knowledge_map=_knowledge_map(),
    )

    curriculum = build_deterministic_curriculum(request)

    assert len(curriculum.weeks) == 6
    assert all(week.estimated_hours <= 8 for week in curriculum.weeks)
    assert curriculum.total_hours <= 48
    assert curriculum.weeks[-1].project_or_application is True


def test_curriculum_prioritizes_weak_missing_and_skips_strong_topics() -> None:
    request = CurriculumGenerationRequest(
        goal="Learn RAG systems",
        timeline_weeks=5,
        hours_per_week=6,
        knowledge_map=_knowledge_map(),
    )

    curriculum = build_deterministic_curriculum(request)
    topic_titles = [topic.title for week in curriculum.weeks for topic in week.topics]

    assert "Python basics" not in topic_titles
    assert "Chunking" in topic_titles
    assert "Reranking" in topic_titles
    assert any(topic.priority == "high" for week in curriculum.weeks for topic in week.topics)


def test_curriculum_shape_validation_passes_for_planner_output() -> None:
    request = CurriculumGenerationRequest(
        goal="Learn RAG systems",
        timeline_weeks=4,
        hours_per_week=5,
        knowledge_map=_knowledge_map(),
    )

    curriculum = build_deterministic_curriculum(request)
    issues = validate_curriculum_plan(curriculum)

    assert issues == []

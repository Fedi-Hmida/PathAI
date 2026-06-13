from app.assessment.schemas import KnowledgeMap
from app.curriculum.planner import build_deterministic_curriculum
from app.curriculum.schemas import CurriculumGenerationRequest, CurriculumPlan
from app.progress.schemas import ProgressInitializeRequest, ProgressUpdateRequest
from app.progress.service import ProgressService


def _curriculum() -> CurriculumPlan:
    return build_deterministic_curriculum(
        CurriculumGenerationRequest(
            goal="Learn RAG systems",
            timeline_weeks=4,
            hours_per_week=6,
            knowledge_map=KnowledgeMap(
                strong=["Python basics"],
                weak=["Embeddings"],
                missing=["Chunking", "Reranking"],
                recommended_level="beginner",
                confidence_score=0.84,
                assessment_notes=["Progress test map."],
            ),
        )
    )


def test_progress_initializes_from_curriculum() -> None:
    service = ProgressService()
    response = service.initialize_progress(
        ProgressInitializeRequest(curriculum=_curriculum())
    )

    summary = response.summary
    assert summary.analytics.total_week_count == 4
    assert summary.analytics.total_topic_count >= 4
    assert summary.analytics.completion_percentage == 0
    assert summary.weeks[0].status == "pending"
    assert summary.events[0].event == "initialized"


def test_progress_updates_topic_and_completion_percentage() -> None:
    service = ProgressService()
    summary = service.initialize_progress(
        ProgressInitializeRequest(curriculum=_curriculum())
    ).summary
    first_topic = summary.weeks[0].topics[0]

    updated = service.update_progress(
        ProgressUpdateRequest(
            curriculum_id=summary.curriculum_id,
            week_number=1,
            topic_id=first_topic.topic_id,
            status="done",
        )
    ).summary

    assert updated.weeks[0].topics[0].status == "done"
    assert updated.weeks[0].completion_percentage > 0
    assert updated.analytics.completed_topic_count == 1


def test_progress_detects_stuck_topics_and_low_quiz_signal() -> None:
    service = ProgressService()
    summary = service.initialize_progress(
        ProgressInitializeRequest(curriculum=_curriculum())
    ).summary
    stuck_targets = [
        (week.week_number, topic.topic_id)
        for week in summary.weeks
        for topic in week.topics
    ][:2]

    for week_number, topic_id in stuck_targets:
        summary = service.update_progress(
            ProgressUpdateRequest(
                curriculum_id=summary.curriculum_id,
                week_number=week_number,
                topic_id=topic_id,
                status="stuck",
            )
        ).summary

    summary = service.update_progress(
        ProgressUpdateRequest(
            curriculum_id=summary.curriculum_id,
            week_number=stuck_targets[0][0],
            topic_id=stuck_targets[0][1],
            event="quiz_completed",
            value={"score": 0.4},
        )
    ).summary

    signals = {signal.signal for signal in summary.analytics.signals}
    assert "repeated_stuck_topics" in signals
    assert "low_quiz_score" in signals
    assert summary.analytics.stuck_topic_count >= 2


def test_progress_week_summary_returns_current_week() -> None:
    service = ProgressService()
    summary = service.initialize_progress(
        ProgressInitializeRequest(curriculum=_curriculum())
    ).summary

    week = service.get_week(summary.curriculum_id, 1).week

    assert week.week_number == 1
    assert week.topics

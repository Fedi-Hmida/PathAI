from app.adapter.schemas import AdaptationCheckRequest
from app.adapter.signals import analyze_adaptation_signals
from app.assessment.schemas import KnowledgeMap
from app.curriculum.planner import build_deterministic_curriculum
from app.curriculum.schemas import CurriculumGenerationRequest, CurriculumPlan
from app.progress.schemas import CurriculumProgressSummary, ProgressInitializeRequest
from app.progress.service import ProgressService
from app.quiz.schemas import QuizAttempt, QuizHistorySummary


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
                assessment_notes=["Adapter signal test map."],
            ),
        )
    )


def _progress(curriculum: CurriculumPlan) -> CurriculumProgressSummary:
    return ProgressService().initialize_progress(
        ProgressInitializeRequest(curriculum=curriculum)
    ).summary


def test_adapter_detects_low_quiz_and_behind_schedule() -> None:
    curriculum = _curriculum()
    progress = _progress(curriculum)
    quiz_history = QuizHistorySummary(
        curriculum_id=curriculum.curriculum_id,
        attempts=[
            QuizAttempt(
                quiz_id="quiz-1",
                curriculum_id=curriculum.curriculum_id,
                week_number=1,
                score=0.4,
                passed=False,
            )
        ],
        best_score=0.4,
        average_score=0.4,
        low_score_count=1,
    )

    decision = analyze_adaptation_signals(
        AdaptationCheckRequest(
            curriculum=curriculum,
            progress_summary=progress,
            quiz_history=quiz_history,
            expected_week_number=1,
        )
    )

    reasons = {signal.reason for signal in decision.signals}
    assert decision.should_replan is True
    assert decision.trigger_reason == "low_quiz_score"
    assert "low_quiz_score" in reasons
    assert "behind_schedule" in reasons
    assert decision.affected_weeks


def test_adapter_detects_repeated_stuck_topics() -> None:
    curriculum = _curriculum()
    progress = _progress(curriculum)
    first_week = progress.weeks[0]
    first_topic = first_week.topics[0].model_copy(update={"status": "stuck"})
    second_topic = first_topic.model_copy(
        update={
            "topic_id": f"{first_topic.topic_id}-extra",
            "topic_name": f"{first_topic.topic_name} extra practice",
            "status": "stuck",
        }
    )
    stuck_week = first_week.model_copy(
        update={"topics": [first_topic, second_topic], "status": "stuck"},
        deep=True,
    )
    progress = progress.model_copy(
        update={"weeks": [stuck_week, *progress.weeks[1:]], "current_week_number": 1},
        deep=True,
    )

    decision = analyze_adaptation_signals(
        AdaptationCheckRequest(curriculum=curriculum, progress_summary=progress)
    )

    assert decision.trigger_reason == "repeated_stuck_topics"
    assert len(decision.affected_topics) == 2
    assert decision.should_replan is True


def test_adapter_no_adaptation_needed_path() -> None:
    curriculum = _curriculum()
    progress = _progress(curriculum)

    decision = analyze_adaptation_signals(
        AdaptationCheckRequest(curriculum=curriculum, progress_summary=progress)
    )

    assert decision.should_replan is False
    assert decision.trigger_reason == "none"
    assert decision.flow == ["adapter"]

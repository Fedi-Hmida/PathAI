import pytest

from app.adapter.schemas import AdaptationReplanRequest
from app.adapter.service import AdapterService
from app.assessment.schemas import KnowledgeMap
from app.curriculum.planner import build_deterministic_curriculum
from app.curriculum.schemas import CurriculumGenerationRequest, CurriculumPlan
from app.progress.schemas import ProgressInitializeRequest, ProgressUpdateRequest
from app.progress.service import ProgressService
from app.quiz.schemas import QuizAnswer, QuizGenerationRequest, QuizSubmissionRequest
from app.quiz.service import QuizService
from app.rag.schemas import CurriculumResourceAttachmentRequest
from app.rag.service import ResourceService


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
                assessment_notes=["Adapter service test map."],
            ),
        )
    )


@pytest.mark.asyncio
async def test_adapter_replan_pipeline_preserves_completed_week_and_runs_critic() -> None:
    curriculum = _curriculum()
    resource_attachment = ResourceService().retrieve_for_curriculum(
        CurriculumResourceAttachmentRequest(curriculum=curriculum, top_k=2)
    )
    progress_service = ProgressService()
    progress = progress_service.initialize_progress(
        ProgressInitializeRequest(curriculum=curriculum)
    ).summary
    completed_topic = progress.weeks[0].topics[0]
    progress = progress_service.update_progress(
        ProgressUpdateRequest(
            curriculum_id=progress.curriculum_id,
            week_number=1,
            topic_id=completed_topic.topic_id,
            status="done",
        )
    ).summary

    quiz_service = QuizService()
    quiz = (
        await quiz_service.generate_quiz(
            QuizGenerationRequest(curriculum=curriculum, week_number=2)
        )
    ).quiz
    quiz_service.submit_quiz(
        quiz.quiz_id,
        QuizSubmissionRequest(
            answers=[
                QuizAnswer(question_id=question.question_id, answer="wrong")
                for question in quiz.questions
            ]
        ),
    )

    result = await AdapterService().run_replan(
        AdaptationReplanRequest(
            curriculum=curriculum,
            progress_summary=progress,
            quiz_history=quiz_service.get_history(curriculum.curriculum_id),
            existing_resource_attachment=resource_attachment,
            expected_week_number=2,
        )
    )

    assert result.decision.decision == "replanned"
    assert result.curriculum_after is not None
    assert result.curriculum_diff is not None
    assert 1 in result.curriculum_diff.preserved_week_numbers
    assert result.resource_refresh_summary is not None
    assert result.resource_refresh_summary.used_existing_unaffected_resources is True
    assert result.critic_review is not None
    assert result.notification is not None
    assert result.adaptation_log.critic_approved == result.critic_review.approved


@pytest.mark.asyncio
async def test_adapter_history_and_no_replan_path() -> None:
    curriculum = _curriculum()
    progress = ProgressService().initialize_progress(
        ProgressInitializeRequest(curriculum=curriculum)
    ).summary
    service = AdapterService()

    result = await service.run_replan(
        AdaptationReplanRequest(curriculum=curriculum, progress_summary=progress)
    )
    loaded = service.get_adaptation(result.adaptation_id)
    history = service.get_history(curriculum.curriculum_id)

    assert result.decision.should_replan is False
    assert result.curriculum_after is None
    assert loaded.adaptation_id == result.adaptation_id
    assert len(history.adaptations) == 1

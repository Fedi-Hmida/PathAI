import pytest

from app.adapter.errors import AdapterNotFoundError
from app.adapter.schemas import AdaptationCheckRequest, AdaptationReplanRequest
from app.adapter.service import AdapterService, RepositoryBackedAdaptationStore
from app.assessment.schemas import KnowledgeMap
from app.curriculum.planner import build_deterministic_curriculum
from app.curriculum.schemas import CurriculumGenerationRequest, CurriculumPlan
from app.progress.errors import ProgressNotFoundError
from app.progress.schemas import ProgressInitializeRequest, ProgressUpdateRequest
from app.progress.service import ProgressService, RepositoryBackedProgressStore
from app.quiz.errors import QuizNotFoundError
from app.quiz.schemas import QuizAnswer, QuizGenerationRequest, QuizSubmissionRequest
from app.quiz.service import QuizService, RepositoryBackedQuizStore
from app.repositories import (
    FakeAdapterRepository,
    FakeProgressRepository,
    FakeQuizRepository,
)


def _curriculum() -> CurriculumPlan:
    return build_deterministic_curriculum(
        CurriculumGenerationRequest(
            goal="Learn RAG systems for a graduation project",
            timeline_weeks=4,
            hours_per_week=6,
            knowledge_map=KnowledgeMap(
                strong=["Python basics"],
                weak=["Embeddings"],
                missing=["Vector search", "Reranking"],
                recommended_level="intermediate",
                confidence_score=0.84,
                assessment_notes=["Repository migration test map."],
            ),
        )
    )


def test_progress_service_uses_injected_repository() -> None:
    repository = FakeProgressRepository()
    service = ProgressService(repository=repository)
    curriculum = _curriculum()

    initialized = service.initialize_progress(
        ProgressInitializeRequest(curriculum=curriculum)
    ).summary
    first_topic = initialized.weeks[0].topics[0]
    updated = service.update_progress(
        ProgressUpdateRequest(
            curriculum_id=initialized.curriculum_id,
            week_number=1,
            topic_id=first_topic.topic_id,
            status="done",
        )
    )
    fetched = service.get_summary(initialized.curriculum_id)
    stored = repository.get_progress(initialized.curriculum_id)
    events = repository.list_events(initialized.curriculum_id)

    assert stored is not None
    assert fetched.analytics.completed_topic_count == 1
    assert updated.event.event == "marked_done"
    assert [event["event"] for event in events] == ["initialized", "marked_done"]


def test_repository_backed_progress_store_keeps_clear_compatibility() -> None:
    repository = FakeProgressRepository()
    service = ProgressService(store=RepositoryBackedProgressStore(repository))
    curriculum = _curriculum()

    summary = service.initialize_progress(
        ProgressInitializeRequest(curriculum=curriculum)
    ).summary
    assert service.get_summary(summary.curriculum_id).curriculum_id == summary.curriculum_id

    service.store.clear()
    with pytest.raises(ProgressNotFoundError):
        service.get_summary(summary.curriculum_id)


@pytest.mark.asyncio
async def test_quiz_service_uses_injected_repository() -> None:
    repository = FakeQuizRepository()
    service = QuizService(repository=repository)
    curriculum = _curriculum()

    quiz = (
        await service.generate_quiz(
            QuizGenerationRequest(
                curriculum=curriculum,
                week_number=1,
                question_count=3,
            )
        )
    ).quiz
    result = service.submit_quiz(
        quiz.quiz_id,
        QuizSubmissionRequest(
            answers=[
                QuizAnswer(
                    question_id=question.question_id,
                    answer=question.correct_answer,
                )
                for question in quiz.questions
            ]
        ),
    )
    history = service.get_history(curriculum.curriculum_id)

    assert repository.get_quiz(quiz.quiz_id) is not None
    assert repository.get_history(curriculum.curriculum_id)[0]["quiz_id"] == quiz.quiz_id
    assert result.score == 1.0
    assert history.best_score == 1.0
    assert history.low_score_count == 0


@pytest.mark.asyncio
async def test_repository_backed_quiz_store_keeps_clear_compatibility() -> None:
    repository = FakeQuizRepository()
    service = QuizService(store=RepositoryBackedQuizStore(repository))
    curriculum = _curriculum()

    quiz = (
        await service.generate_quiz(
            QuizGenerationRequest(curriculum=curriculum, week_number=1)
        )
    ).quiz
    assert service.get_quiz(quiz.quiz_id).quiz_id == quiz.quiz_id

    service.store.clear()
    with pytest.raises(QuizNotFoundError):
        service.get_quiz(quiz.quiz_id)


@pytest.mark.asyncio
async def test_adapter_service_uses_injected_repository() -> None:
    repository = FakeAdapterRepository()
    service = AdapterService(repository=repository)
    curriculum = _curriculum()
    progress = ProgressService().initialize_progress(
        ProgressInitializeRequest(curriculum=curriculum)
    ).summary

    decision = service.check_adaptation(
        AdaptationCheckRequest(curriculum=curriculum, progress_summary=progress)
    )
    result = await service.run_replan(
        AdaptationReplanRequest(curriculum=curriculum, progress_summary=progress)
    )
    loaded = service.get_adaptation(result.adaptation_id)
    history = service.get_history(curriculum.curriculum_id)

    assert decision.should_replan is False
    assert repository.get_adaptation_result(result.adaptation_id) is not None
    assert loaded.adaptation_id == result.adaptation_id
    assert len(history.adaptations) == 1


@pytest.mark.asyncio
async def test_repository_backed_adaptation_store_keeps_clear_compatibility() -> None:
    repository = FakeAdapterRepository()
    service = AdapterService(store=RepositoryBackedAdaptationStore(repository))
    curriculum = _curriculum()
    progress = ProgressService().initialize_progress(
        ProgressInitializeRequest(curriculum=curriculum)
    ).summary

    result = await service.run_replan(
        AdaptationReplanRequest(curriculum=curriculum, progress_summary=progress)
    )
    assert service.get_adaptation(result.adaptation_id).adaptation_id == (
        result.adaptation_id
    )

    service.store.clear()
    with pytest.raises(AdapterNotFoundError):
        service.get_adaptation(result.adaptation_id)

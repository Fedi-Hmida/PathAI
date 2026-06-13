import pytest

from app.assessment.schemas import AnswerSubmissionRequest, GoalIntakeRequest, KnowledgeMap
from app.assessment.service import AssessmentService, RepositoryBackedAssessmentStore
from app.curriculum.schemas import CurriculumGenerationRequest
from app.curriculum.service import CurriculumService, RepositoryBackedCurriculumStore
from app.repositories import FakeAssessmentRepository, FakeCurriculumRepository


@pytest.mark.asyncio
async def test_assessment_service_uses_injected_repository() -> None:
    repository = FakeAssessmentRepository()
    service = AssessmentService(repository=repository)

    started = await service.start_assessment(
        GoalIntakeRequest(
            goal="Learn RAG systems",
            timeline_weeks=4,
            hours_per_week=6,
            target_level="intermediate",
        )
    )
    stored_started = repository.get_session(started.session.session_id)
    answered = await service.submit_answer(
        started.session.session_id,
        AnswerSubmissionRequest(answer="Embeddings represent text for semantic search."),
    )
    finalized = service.finalize_assessment(started.session.session_id)
    stored_finalized = repository.get_session(started.session.session_id)

    assert stored_started is not None
    assert stored_started["status"] == "in_progress"
    assert answered.evaluation is not None
    assert stored_finalized is not None
    assert stored_finalized["status"] == "completed"
    assert stored_finalized["knowledge_map"] is not None
    assert finalized.result.status == "completed"


def test_repository_backed_assessment_store_keeps_clear_compatibility() -> None:
    repository = FakeAssessmentRepository()
    store = RepositoryBackedAssessmentStore(repository)

    repository.create_session(
        {
            "session_id": "session-1",
            "goal": "Learn RAG systems",
            "timeline_weeks": 4,
            "hours_per_week": 6,
            "target_level": "intermediate",
            "question_index": 1,
            "max_questions": 3,
            "confidence_score": 0,
            "status": "in_progress",
            "current_difficulty": "beginner",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
    )

    assert store.load("session-1") is not None
    store.clear()
    assert store.load("session-1") is None


@pytest.mark.asyncio
async def test_curriculum_service_uses_injected_repository() -> None:
    repository = FakeCurriculumRepository()
    service = CurriculumService(repository=repository)

    response = await service.generate_curriculum(
        CurriculumGenerationRequest(
            assessment_session_id="session-1",
            goal="Learn RAG systems",
            timeline_weeks=4,
            hours_per_week=6,
            knowledge_map=KnowledgeMap(
                strong=["Python basics"],
                weak=["Embeddings"],
                missing=["Reranking"],
                recommended_level="beginner",
                confidence_score=0.82,
                assessment_notes=["Repository migration test."],
            ),
        )
    )
    curriculum = response.result.curriculum
    stored = repository.get_curriculum(curriculum.curriculum_id)
    by_session = repository.list_by_session("session-1")

    assert stored is not None
    assert stored["curriculum_id"] == curriculum.curriculum_id
    assert stored["assessment_session_id"] == "session-1"
    assert by_session[0]["curriculum_id"] == curriculum.curriculum_id
    assert service.get_curriculum(curriculum.curriculum_id).curriculum.curriculum_id == (
        curriculum.curriculum_id
    )


def test_repository_backed_curriculum_store_keeps_clear_compatibility() -> None:
    repository = FakeCurriculumRepository()
    store = RepositoryBackedCurriculumStore(repository)

    repository.save_curriculum(
        {
            "curriculum_id": "curriculum-1",
            "goal": "Learn RAG systems",
            "timeline_weeks": 4,
            "hours_per_week": 6,
            "knowledge_map": {
                "strong": [],
                "weak": ["Embeddings"],
                "missing": [],
                "recommended_level": "beginner",
                "confidence_score": 0.8,
                "assessment_notes": [],
            },
            "weeks": [
                {
                    "week_number": 1,
                    "theme": "Embeddings",
                    "weekly_goal": "Understand embeddings.",
                    "milestone": {
                        "title": "Embedding check",
                        "description": "Explain embeddings.",
                        "deliverable": "Short note.",
                        "evaluation_hint": "Look for semantic-search language.",
                    },
                    "estimated_hours": 6,
                    "difficulty": "beginner",
                    "topics": [
                            {
                                "topic_id": "topic-1",
                                "title": "Embeddings",
                                "priority": "high",
                            "difficulty": "beginner",
                            "estimated_hours": 6,
                            "rationale": "Needed for RAG.",
                            "subtopics": [
                                {
                                    "title": "Vector meaning",
                                    "estimated_hours": 2,
                                    "learning_outcome": "Define an embedding.",
                                }
                            ],
                            "learning_outcomes": ["Define embeddings."],
                        }
                    ],
                }
            ],
            "total_hours": 6,
            "difficulty_progression": {
                "starting_level": "beginner",
                "ending_level": "beginner",
                "weekly_levels": ["beginner"],
                "rationale": "Single-week fixture.",
            },
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
    )

    assert store.load("curriculum-1") is not None
    store.clear()
    assert store.load("curriculum-1") is None

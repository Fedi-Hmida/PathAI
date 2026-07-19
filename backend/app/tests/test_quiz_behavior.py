from __future__ import annotations

import re
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.agents.deterministic.quiz import score_quiz_attempt
from app.agents.mock import MockQuizAgent
from app.agents.services.quiz import QuizAgentService
from app.api.v1.dependencies import ApiServiceContainer, reset_api_container_for_tests
from app.api.v1.quiz import _to_learner_quiz, get_quiz_attempt_review
from app.core.settings import get_settings
from app.fixtures import canonical_demo as demo
from app.main import create_app
from app.repositories.errors import NotFoundError
from app.schemas.curriculum import (
    CurriculumDTO,
    CurriculumTopicDTO,
    CurriculumWeekDTO,
)
from app.schemas.enums import (
    CurriculumStatus,
    DifficultyLevel,
    ProgressStatus,
    QuestionType,
    QuizAttemptStatus,
    TopicProgressStatus,
)
from app.schemas.progress import ProgressStateDTO, TopicProgressDTO
from app.schemas.quiz import (
    LearnerQuizQuestionDTO,
    QuizAgentInput,
    QuizAgentOutput,
    QuizAnswerSubmission,
    QuizAttemptDTO,
    QuizDTO,
    QuizScoreOutput,
)
from app.services.authorization import AuthorizationService

_RAG_TOKEN_PATTERN = re.compile(
    r"\b(rag|retrieval|reranking|chunking|embeddings?|vector[_ ]search|hallucination)\b",
    re.IGNORECASE,
)


def test_quiz_generation_targets_real_curriculum_concepts_and_drops_unmatched() -> None:
    output = _build_quiz_output(
        [
            "retrieval_evaluation",
            "vector_search",
            "chunking",
            "reranking",
            "production_rag_failures",
        ],
    )
    question_ids = [question.question_id for question in output.questions]
    concept_ids = {concept for question in output.questions for concept in question.concept_ids}

    assert QuizAgentOutput.model_validate(output) == output
    # "reranking" isn't a concept in the demo curriculum's topics - it must be
    # dropped, not silently swapped for any other RAG concept.
    assert "reranking" not in concept_ids
    assert {"retrieval_evaluation", "vector_search", "chunking", "production_rag_failures"} <= (
        concept_ids
    )
    assert question_ids == [
        "question_quiz_retrieval_evaluation",
        "question_quiz_vector_search",
        "question_quiz_chunking",
        "question_quiz_production_rag_failures",
        "question_quiz_rag_fundamentals",
    ]
    for question in output.questions:
        assert question.question_type == QuestionType.MULTIPLE_CHOICE
        assert question.correct_answer in question.options


def test_quiz_scoring_is_deterministic_and_sets_feedback_signals() -> None:
    quiz, attempt = _build_persisted_quiz_and_attempt()
    score_output = QuizScoreOutput(
        total_score=attempt.total_score,
        correct_count=attempt.correct_count,
        total_questions=attempt.total_questions,
        concept_scores=attempt.concept_scores,
        weak_concepts=attempt.weak_concepts,
        feedback=attempt.feedback or "",
    )

    assert score_output.total_score < 0.65
    assert attempt.adaptation_triggered is True
    assert "vector_search" in attempt.weak_concepts
    assert "rag_fundamentals" in attempt.weak_concepts
    assert "Review these concepts" in (attempt.feedback or "")
    assert len(attempt.answers) == len(quiz.questions)


def test_learner_quiz_output_does_not_expose_answer_keys() -> None:
    quiz, _attempt = _build_persisted_quiz_and_attempt()
    learner_quiz = _to_learner_quiz(quiz)
    payload = learner_quiz.model_dump()

    assert payload["quiz_id"] == demo.QUIZ_ID
    assert "correct_answer" not in str(payload)
    assert "explanation" not in str(payload)


def test_get_attempt_for_quiz_returns_the_attempt_when_ids_match() -> None:
    container = ApiServiceContainer()
    agent_service = QuizAgentService(MockQuizAgent(), container.quiz_service)
    goal = container.goal_service.create(demo.LEARNING_GOAL)
    curriculum = container.curriculum_service.create(demo.CURRICULUM)
    progress = container.progress_service.create(demo.PROGRESS_STATE)
    _quiz, attempt = agent_service.build(goal, curriculum, progress)

    fetched = container.quiz_service.get_attempt_for_quiz(attempt.quiz_id, attempt.quiz_attempt_id)

    assert fetched == attempt


def test_get_attempt_for_quiz_404s_when_attempt_belongs_to_a_different_quiz() -> None:
    """A real attempt ID under the wrong quiz ID must 404 like a missing
    attempt, not reveal that it exists elsewhere - the same "don't leak
    which part failed" property `AuthorizationService` already enforces."""
    container = ApiServiceContainer()
    agent_service = QuizAgentService(MockQuizAgent(), container.quiz_service)
    goal = container.goal_service.create(demo.LEARNING_GOAL)
    curriculum = container.curriculum_service.create(demo.CURRICULUM)
    progress = container.progress_service.create(demo.PROGRESS_STATE)
    _quiz_a, attempt_a = agent_service.build(goal, curriculum, progress)
    quiz_b, _attempt_b = agent_service.build(
        goal,
        curriculum,
        progress,
        quiz_id="quiz_other_review_test",
        quiz_attempt_id="attempt_other_review_test",
    )

    with pytest.raises(NotFoundError):
        container.quiz_service.get_attempt_for_quiz(quiz_b.quiz_id, attempt_a.quiz_attempt_id)


def test_quiz_attempt_review_strips_answer_key_until_the_attempt_is_scored() -> None:
    """The schema allows a non-SCORED attempt (the deferred Quiz Taking
    flow); today's `generate()` pipeline always produces a SCORED attempt,
    so this branch can't be exercised live - exercise it directly instead."""
    container = ApiServiceContainer()
    agent_service = QuizAgentService(MockQuizAgent(), container.quiz_service)
    goal = container.goal_service.create(demo.LEARNING_GOAL)
    curriculum = container.curriculum_service.create(demo.CURRICULUM)
    progress = container.progress_service.create(demo.PROGRESS_STATE)
    quiz, attempt = agent_service.build(goal, curriculum, progress)
    submitted_attempt = container.quiz_service.save_attempt(
        attempt.model_copy(update={"status": QuizAttemptStatus.SUBMITTED}),
    )
    authz = AuthorizationService(container.goal_repository)

    review = get_quiz_attempt_review(
        quiz.quiz_id,
        submitted_attempt.quiz_attempt_id,
        container.quiz_service,
        None,
        authz,
    )

    assert review.attempt.status == QuizAttemptStatus.SUBMITTED
    assert all(isinstance(question, LearnerQuizQuestionDTO) for question in review.questions)
    payload = str([question.model_dump() for question in review.questions])
    assert "correct_answer" not in payload
    assert "explanation" not in payload


def test_quiz_attempt_review_route_returns_full_answer_keyed_data_for_a_scored_attempt() -> None:
    client = _client()
    _load_demo(client)

    response = client.get(f"/api/v1/quizzes/{demo.QUIZ_ID}/attempts/{demo.QUIZ_ATTEMPT_ID}")

    assert response.status_code == 200
    body = response.json()
    assert body["attempt"]["quiz_attempt_id"] == demo.QUIZ_ATTEMPT_ID
    assert body["attempt"]["status"] == "scored"
    assert body["questions"][0]["correct_answer"]
    assert "explanation" in body["questions"][0]


def test_quiz_attempt_review_route_404s_on_quiz_attempt_mismatch() -> None:
    client = _client()
    _load_demo(client)

    response = client.get(
        f"/api/v1/quizzes/quiz_not_the_real_owner/attempts/{demo.QUIZ_ATTEMPT_ID}"
    )

    assert response.status_code == 404


@pytest.fixture
def _auth_enabled_app(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("PATHAI_ENABLE_AUTH", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "quiz-attempt-review-test-secret-0123456789")
    monkeypatch.setenv("REFRESH_COOKIE_SECURE", "false")
    get_settings.cache_clear()
    reset_api_container_for_tests()
    yield
    get_settings.cache_clear()


def test_quiz_attempt_review_route_denies_a_different_owners_attempt_with_404(
    _auth_enabled_app: None,
) -> None:
    client = TestClient(create_app())
    owner_token = _register(client, "quiz-review-owner@example.com")
    _create_workspace(client, owner_token)
    _complete_assessment(client, owner_token)
    generated = client.post(
        "/api/v1/me/workspace/generate", headers=_auth_header(owner_token)
    ).json()
    quiz_id = generated["quiz_id"]
    attempt_id = generated["quiz_attempt_id"]

    owner_response = client.get(
        f"/api/v1/quizzes/{quiz_id}/attempts/{attempt_id}",
        headers=_auth_header(owner_token),
    )
    assert owner_response.status_code == 200
    assert owner_response.json()["questions"][0]["correct_answer"]

    other_token = _register(client, "quiz-review-other@example.com")

    other_response = client.get(
        f"/api/v1/quizzes/{quiz_id}/attempts/{attempt_id}",
        headers=_auth_header(other_token),
    )

    # Denied with the same 404 a truly-missing attempt would return - never
    # a 403, and never a 200 leaking the owner's answer-keyed data.
    assert other_response.status_code == 404
    assert other_response.json() != owner_response.json()


def _client() -> TestClient:
    reset_api_container_for_tests()
    return TestClient(create_app())


def _load_demo(client: TestClient) -> None:
    response = client.post("/api/v1/demo/load-fixtures")
    assert response.status_code == 200


def _register(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correcthorsebattery"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]  # type: ignore[no-any-return]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_workspace(client: TestClient, token: str) -> None:
    response = client.post(
        "/api/v1/me/workspace",
        headers=_auth_header(token),
        json={"goal_text": "Learn classical guitar for a wedding performance"},
    )
    assert response.status_code == 201


def _complete_assessment(client: TestClient, token: str) -> None:
    start = client.post("/api/v1/me/assessment/start", headers=_auth_header(token))
    assessment_id = start.json()["assessment_session_id"]
    question_id = start.json()["current_question"]["question_id"]
    for _ in range(5):
        response = client.post(
            f"/api/v1/me/assessment/{assessment_id}/answer",
            headers=_auth_header(token),
            json={"question_id": question_id, "selected_options": [], "self_rating": 3},
        )
        next_question = response.json()["session"]["current_question"]
        if next_question is not None:
            question_id = next_question["question_id"]


def test_quiz_agent_service_never_falls_back_to_the_demo_target_concepts() -> None:
    """A first-time learner with no progress yet (empty weak_concepts) must
    get a quiz targeting their own curriculum's concepts, never the canonical
    demo's fixed RAG concept list - the old service-layer fallback this
    guards against."""
    container = ApiServiceContainer()
    service = QuizAgentService(MockQuizAgent(), container.quiz_service)
    goal = container.goal_service.create(demo.LEARNING_GOAL.model_copy(
        update={"goal_id": "goal_budgeting", "goal_text": "Learn personal budgeting"},
    ))
    curriculum = container.curriculum_service.create(_budgeting_curriculum())
    progress = ProgressStateDTO(
        progress_state_id="progress_budgeting",
        goal_id=goal.goal_id,
        curriculum_id=curriculum.curriculum_id,
        status=ProgressStatus.NOT_STARTED,
        overall_completion=0.0,
        topic_progress=[
            TopicProgressDTO(
                topic_id="topic_budgeting_basics",
                status=TopicProgressStatus.NOT_STARTED,
                completion=0.0,
            ),
        ],
        weak_concepts=[],
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )

    quiz, _attempt = service.build(goal, curriculum, progress)

    demo_concepts = set(demo.QUIZ.target_concept_ids)
    assert set(quiz.target_concept_ids) & demo_concepts == set()
    assert set(quiz.target_concept_ids) == {"budgeting_basics", "emergency_fund"}
    for question in quiz.questions:
        haystack = " ".join(
            [
                question.prompt,
                question.correct_answer,
                question.explanation or "",
                *question.options,
            ],
        )
        assert not _RAG_TOKEN_PATTERN.search(haystack), haystack


def test_quiz_for_a_non_rag_goal_never_mentions_rag_vocabulary() -> None:
    topics = _budgeting_topics()
    output = MockQuizAgent().build_quiz(
        QuizAgentInput(
            goal_text="Learn personal budgeting and how to build an emergency fund",
            curriculum_topics=topics,
            target_concepts=["budgeting_basics", "emergency_fund", "retrieval_evaluation"],
            difficulty=DifficultyLevel.BEGINNER,
            question_count=5,
        ),
    )

    concept_ids = {concept for question in output.questions for concept in question.concept_ids}
    # "retrieval_evaluation" isn't a concept of any budgeting topic - it must be
    # dropped, and the old fixed RAG fallback must never be substituted in.
    assert "retrieval_evaluation" not in concept_ids
    assert concept_ids == {"budgeting_basics", "emergency_fund"}

    for question in output.questions:
        haystack = " ".join(
            [
                question.prompt,
                question.correct_answer,
                question.explanation or "",
                *question.options,
            ],
        )
        assert not _RAG_TOKEN_PATTERN.search(haystack), haystack


def test_quiz_scoring_reflects_the_submitted_answer_not_a_fixed_lookup() -> None:
    topics = _budgeting_topics()
    output = MockQuizAgent().build_quiz(
        QuizAgentInput(
            goal_text="Learn personal budgeting",
            curriculum_topics=topics,
            target_concepts=["budgeting_basics", "emergency_fund"],
            difficulty=DifficultyLevel.BEGINNER,
            question_count=2,
        ),
    )
    budgeting_question = next(
        question for question in output.questions if "budgeting_basics" in question.concept_ids
    )
    emergency_question = next(
        question for question in output.questions if "emergency_fund" in question.concept_ids
    )

    correct_attempt = _attempt_with_answers(
        [
            QuizAnswerSubmission(
                question_id=budgeting_question.question_id,
                selected_options=[budgeting_question.correct_answer],
            ),
            QuizAnswerSubmission(
                question_id=emergency_question.question_id,
                selected_options=[emergency_question.correct_answer],
            ),
        ],
    )
    wrong_attempt = _attempt_with_answers(
        [
            QuizAnswerSubmission(
                question_id=budgeting_question.question_id,
                selected_options=["Something else entirely"],
            ),
            QuizAnswerSubmission(
                question_id=emergency_question.question_id,
                selected_options=["Something else entirely"],
            ),
        ],
    )

    correct_score = score_quiz_attempt(correct_attempt, output.questions)
    wrong_score = score_quiz_attempt(wrong_attempt, output.questions)

    assert correct_score.total_score == 1.0
    assert correct_score.weak_concepts == []
    assert wrong_score.total_score == 0.0
    assert set(wrong_score.weak_concepts) == {"budgeting_basics", "emergency_fund"}


def _budgeting_topics() -> list[CurriculumTopicDTO]:
    return [
        CurriculumTopicDTO(
            topic_id="topic_budgeting_basics",
            title="Budgeting basics",
            description="Build a simple monthly budget from income and fixed expenses.",
            concept_ids=["budgeting_basics"],
            difficulty=DifficultyLevel.BEGINNER,
            estimated_hours=2.0,
            learning_outcomes=["Create a first monthly budget."],
            sequence_order=1,
        ),
        CurriculumTopicDTO(
            topic_id="topic_emergency_fund",
            title="Emergency fund planning",
            description="Size and build an emergency fund for unplanned expenses.",
            concept_ids=["emergency_fund"],
            difficulty=DifficultyLevel.BEGINNER,
            estimated_hours=1.5,
            learning_outcomes=["Set a target emergency fund size."],
            sequence_order=2,
        ),
    ]


def _budgeting_curriculum() -> CurriculumDTO:
    return CurriculumDTO(
        curriculum_id="curriculum_budgeting",
        goal_id="goal_budgeting",
        knowledge_map_id="kmap_budgeting",
        run_id="run_budgeting",
        status=CurriculumStatus.ACTIVE,
        title="Personal Budgeting Fundamentals",
        duration_weeks=1,
        target_outcomes=["Build a monthly budget and an emergency fund."],
        created_at=demo.NOW,
        updated_at=demo.NOW,
        weeks=[
            CurriculumWeekDTO(
                week_id="week_budgeting",
                week_number=1,
                theme="Budgeting foundations",
                estimated_hours=3.5,
                learning_outcomes=["Build a first monthly budget and emergency fund plan."],
                topics=_budgeting_topics(),
            ),
        ],
    )


def _attempt_with_answers(answers: list[QuizAnswerSubmission]) -> QuizAttemptDTO:
    return QuizAttemptDTO(
        quiz_attempt_id=demo.QUIZ_ATTEMPT_ID,
        quiz_id=demo.QUIZ_ID,
        goal_id=demo.GOAL_ID,
        curriculum_id=demo.CURRICULUM_ID,
        answers=answers,
        total_score=0.0,
        correct_count=0,
        total_questions=len(answers),
        concept_scores=[demo.QUIZ_ATTEMPT.concept_scores[0].model_copy(deep=True)],
        submitted_at=demo.NOW,
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )


def _build_quiz_output(target_concepts: list[str]) -> QuizAgentOutput:
    return MockQuizAgent().build_quiz(
        QuizAgentInput(
            goal_text=demo.CANONICAL_GOAL_TEXT,
            curriculum_topics=_topics(demo.CURRICULUM),
            target_concepts=target_concepts,
            difficulty=DifficultyLevel.INTERMEDIATE,
            question_count=len(target_concepts),
        ),
    )


def _build_persisted_quiz_and_attempt() -> tuple[QuizDTO, QuizAttemptDTO]:
    container = ApiServiceContainer()
    service = QuizAgentService(MockQuizAgent(), container.quiz_service)
    goal = container.goal_service.create(demo.LEARNING_GOAL)
    curriculum = container.curriculum_service.create(demo.CURRICULUM)
    progress = container.progress_service.create(demo.PROGRESS_STATE)
    return service.build(goal, curriculum, progress)


def _topics(curriculum: CurriculumDTO) -> list[CurriculumTopicDTO]:
    return [topic for week in curriculum.weeks for topic in week.topics]

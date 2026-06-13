from typing import Protocol

from app.assessment.constants import (
    MIN_QUESTIONS_FOR_CONFIDENCE,
    DifficultyLevel,
    new_uuid,
    utc_now,
)
from app.assessment.errors import AssessmentNotFoundError, AssessmentStateError
from app.assessment.llm import generate_assessment_question
from app.assessment.question_bank import build_question_bank, select_question
from app.assessment.rubric import (
    build_knowledge_map,
    compute_confidence,
    evaluate_answer,
    next_difficulty,
)
from app.assessment.schemas import (
    AnswerSubmissionRequest,
    AssessmentQuestion,
    AssessmentSessionState,
    FinalAssessmentResult,
    FinalizeAssessmentResponse,
    GoalIntakeRequest,
    StartAssessmentResponse,
    SubmitAnswerResponse,
)
from app.repositories import AssessmentRepository, FakeAssessmentRepository


class AssessmentStore(Protocol):
    def save(self, session: AssessmentSessionState) -> None:
        ...

    def load(self, session_id: str) -> AssessmentSessionState | None:
        ...

    def clear(self) -> None:
        ...


class RepositoryBackedAssessmentStore:
    def __init__(self, repository: AssessmentRepository | None = None) -> None:
        self.repository = repository or FakeAssessmentRepository()

    def save(self, session: AssessmentSessionState) -> None:
        payload = session.model_dump(mode="json")
        if self.repository.get_session(session.session_id) is None:
            self.repository.create_session(payload)
            return
        self.repository.update_session(session.session_id, payload)

    def load(self, session_id: str) -> AssessmentSessionState | None:
        payload = self.repository.get_session(session_id)
        if payload is None:
            return None
        return AssessmentSessionState.model_validate(payload)

    def clear(self) -> None:
        clear = getattr(self.repository, "clear", None)
        if callable(clear):
            clear()


class InMemoryAssessmentStore(RepositoryBackedAssessmentStore):
    """Backward-compatible fake repository store for tests and local demo routes."""

    def __init__(self) -> None:
        super().__init__(FakeAssessmentRepository())


class AssessmentService:
    def __init__(
        self,
        store: AssessmentStore | None = None,
        repository: AssessmentRepository | None = None,
    ) -> None:
        self.store = store or RepositoryBackedAssessmentStore(repository)

    async def start_assessment(self, request: GoalIntakeRequest) -> StartAssessmentResponse:
        now = utc_now()
        session = AssessmentSessionState(
            session_id=new_uuid(),
            user_id=request.user_id,
            goal_id=request.goal_id or new_uuid(),
            goal=request.goal,
            timeline_weeks=request.timeline_weeks,
            hours_per_week=request.hours_per_week,
            target_level=request.target_level,
            question_index=1,
            max_questions=request.max_questions,
            confidence_score=0.0,
            status="in_progress",
            current_difficulty=_initial_difficulty(request.target_level),
            created_at=now,
            updated_at=now,
        )
        next_question = await self._next_question(session)
        session.questions.append(next_question)
        session.updated_at = utc_now()
        self.store.save(session)
        return StartAssessmentResponse(session=session, next_question=next_question)

    def get_session(self, session_id: str) -> AssessmentSessionState:
        session = self.store.load(session_id)
        if session is None:
            raise AssessmentNotFoundError(session_id)
        return session

    async def submit_answer(
        self,
        session_id: str,
        request: AnswerSubmissionRequest,
    ) -> SubmitAnswerResponse:
        session = self.get_session(session_id)
        if session.status == "completed":
            result = self._build_result(session)
            return SubmitAnswerResponse(session=session, evaluation=None, result=result)

        question = self._current_question(session)
        evaluation = evaluate_answer(question, request.answer)
        session.answers.append(evaluation)
        session.current_difficulty = next_difficulty(session.current_difficulty, evaluation)
        session.confidence_score = self._compute_session_confidence(session)

        if self._should_finalize(session):
            session = self._finalize_session(session)
            self.store.save(session)
            return SubmitAnswerResponse(
                session=session,
                evaluation=evaluation,
                result=self._build_result(session),
            )

        next_question = await self._next_question(session)
        session.questions.append(next_question)
        session.question_index = len(session.answers) + 1
        session.updated_at = utc_now()
        self.store.save(session)
        return SubmitAnswerResponse(
            session=session,
            evaluation=evaluation,
            next_question=next_question,
        )

    def finalize_assessment(self, session_id: str) -> FinalizeAssessmentResponse:
        session = self.get_session(session_id)
        if not session.answers:
            raise AssessmentStateError(
                code="assessment_has_no_answers",
                message="At least one answer is required before finalizing an assessment.",
                status_code=409,
            )
        session = self._finalize_session(session)
        self.store.save(session)
        return FinalizeAssessmentResponse(session=session, result=self._build_result(session))

    async def _next_question(self, session: AssessmentSessionState) -> AssessmentQuestion:
        question_bank = build_question_bank(session.goal, session.target_level)
        asked_ids = {question.question_id for question in session.questions}
        fallback = select_question(question_bank, asked_ids, session.current_difficulty)
        return await generate_assessment_question(
            goal=session.goal,
            fallback_question=fallback,
        )

    def _current_question(self, session: AssessmentSessionState) -> AssessmentQuestion:
        if not session.questions:
            raise AssessmentStateError(
                code="assessment_has_no_question",
                message="Assessment session does not have an active question.",
                status_code=409,
            )
        return session.questions[-1]

    def _should_finalize(self, session: AssessmentSessionState) -> bool:
        if len(session.answers) >= session.max_questions:
            return True
        return (
            len(session.answers) >= MIN_QUESTIONS_FOR_CONFIDENCE
            and session.confidence_score >= 0.82
        )

    def _finalize_session(self, session: AssessmentSessionState) -> AssessmentSessionState:
        session.status = "completed"
        session.question_index = len(session.answers)
        session.knowledge_map = build_knowledge_map(
            answers=session.answers,
            goal=session.goal,
            fallback_level=session.target_level,
            confidence_score=session.confidence_score,
        )
        session.assessment_notes = session.knowledge_map.assessment_notes
        session.updated_at = utc_now()
        return session

    def _build_result(self, session: AssessmentSessionState) -> FinalAssessmentResult:
        if session.knowledge_map is None:
            session = self._finalize_session(session)
        if session.knowledge_map is None:
            raise AssessmentStateError(
                code="knowledge_map_missing",
                message="Assessment could not produce a knowledge map.",
                status_code=500,
            )
        return FinalAssessmentResult(
            session_id=session.session_id,
            knowledge_map=session.knowledge_map,
            progress=session.progress,
        )

    def _compute_session_confidence(self, session: AssessmentSessionState) -> float:
        topic_count = len({answer.topic for answer in session.answers})
        return compute_confidence(
            answer_count=len(session.answers),
            max_questions=session.max_questions,
            topic_count=topic_count,
        )


def _initial_difficulty(target_level: DifficultyLevel) -> DifficultyLevel:
    if target_level == "advanced":
        return "intermediate"
    return "beginner"

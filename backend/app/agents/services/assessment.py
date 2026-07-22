from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from app.agents.contracts import AssessorAgent
from app.agents.deterministic.assessment import (
    assessment_confidence,
    build_completed_session,
    build_scored_answer,
    concept_evidence_from_answers,
    diagnostic_focus_for_goal,
    seeded_answer_for_question,
)
from app.agents.services.common import create_or_get, validate_agent_output
from app.schemas.assessment import (
    AssessmentAgentInput,
    AssessmentAgentOutput,
    AssessmentAnswerCreate,
    AssessmentAnswerDTO,
    AssessmentQuestionDTO,
    AssessmentScoreOutput,
    AssessmentSessionDTO,
    ConceptEvidence,
)
from app.schemas.enums import AssessmentStatus, GoalStatus
from app.schemas.goal import LearningGoalDTO
from app.services import AssessmentService, GoalService

QUESTION_LIMIT = 5


class AssessmentSessionNotActiveError(Exception):
    """Raised when an answer is submitted to a session that isn't in progress."""

    def __init__(self, assessment_session_id: str) -> None:
        self.assessment_session_id = assessment_session_id
        super().__init__(f"assessment session is not active: {assessment_session_id}")


class AssessmentQuestionMismatchError(Exception):
    """Raised when a submitted answer's question doesn't match the session's
    current pending question (stale/duplicate submit)."""

    def __init__(self, assessment_session_id: str) -> None:
        self.assessment_session_id = assessment_session_id
        super().__init__(
            f"submitted question does not match the pending question: {assessment_session_id}",
        )


@dataclass(slots=True)
class AssessmentAgentService:
    agent: AssessorAgent
    assessments: AssessmentService
    goals: GoalService

    def run_diagnostic(self, goal: LearningGoalDTO) -> AssessmentSessionDTO:
        target_concepts = diagnostic_focus_for_goal(goal.goal_text, goal.learner_profile)
        scored_answers: list[AssessmentAnswerDTO] = []
        for _ in range(5):
            question_output = self._generate_question(
                goal=goal,
                target_concepts=target_concepts,
                prior_answers=scored_answers,
            )
            answer = seeded_answer_for_question(goal=goal, question=question_output.question)
            scored_answers.append(self._persist_answer(answer))

        session = build_completed_session(goal=goal, answers=scored_answers)
        saved_session = create_or_get(
            create=self.assessments.create_session,
            get=self.assessments.get_session_by_id,
            record=session,
            record_id=session.assessment_session_id,
        )
        return saved_session

    def get_current_session(self, goal: LearningGoalDTO) -> AssessmentSessionDTO | None:
        """Return the most recent live session for this goal, if any."""
        sessions = self.assessments.list_sessions_by_goal_id(goal.goal_id)
        if not sessions:
            return None
        return sessions[-1]

    def start(self, goal: LearningGoalDTO) -> AssessmentSessionDTO:
        """Start (or resume) a live, turn-by-turn diagnostic for this goal.

        Idempotent: a caller that already has a session for this goal gets that
        session back rather than a second one, so a page refresh or a
        double-submit can't create duplicate sessions.
        """
        existing = self.get_current_session(goal)
        if existing is not None:
            return existing

        target_concepts = diagnostic_focus_for_goal(goal.goal_text, goal.learner_profile)
        question_output = self._generate_question(
            goal=goal,
            target_concepts=target_concepts,
            prior_answers=[],
        )
        session = build_started_session(goal=goal, question=question_output.question)
        saved_session = create_or_get(
            create=self.assessments.create_session,
            get=self.assessments.get_session_by_id,
            record=session,
            record_id=session.assessment_session_id,
        )
        self.goals.update_status(goal.goal_id, GoalStatus.ASSESSMENT_STARTED)
        return saved_session

    def submit_answer(
        self,
        *,
        goal: LearningGoalDTO,
        session: AssessmentSessionDTO,
        answer_create: AssessmentAnswerCreate,
    ) -> tuple[AssessmentSessionDTO, AssessmentAnswerDTO]:
        """Score the learner's answer to the session's current pending question,
        then either advance to the next generated question or complete the
        session once `QUESTION_LIMIT` answers have been recorded (the same
        bound `run_diagnostic` uses)."""
        if session.status != AssessmentStatus.IN_PROGRESS or session.current_question is None:
            raise AssessmentSessionNotActiveError(session.assessment_session_id)
        if session.current_question.question_id != answer_create.question_id:
            raise AssessmentQuestionMismatchError(session.assessment_session_id)

        pending_answer = build_pending_answer(
            goal=goal,
            session=session,
            question=session.current_question,
            answer_create=answer_create,
        )
        scored_answer = self._persist_answer(pending_answer)

        prior_answers = self.assessments.list_answers_by_session_id(
            session.assessment_session_id,
        )
        evidence = concept_evidence_from_answers(prior_answers, goal.learner_profile)
        confidence = assessment_confidence(
            answer_count=len(prior_answers),
            evidence_count=len(evidence),
        )

        if len(prior_answers) >= QUESTION_LIMIT:
            completed_session = build_live_completed_session(
                session=session,
                answers=prior_answers,
                evidence=evidence,
                confidence=confidence,
            )
            saved_session = self.assessments.save_session(completed_session)
        else:
            target_concepts = diagnostic_focus_for_goal(goal.goal_text, goal.learner_profile)
            next_question_output = self._generate_question(
                goal=goal,
                target_concepts=target_concepts,
                prior_answers=prior_answers,
            )
            advanced_session = session.model_copy(
                update={
                    "current_question": next_question_output.question,
                    "question_count": len(prior_answers),
                    "confidence": confidence,
                    "concept_evidence": evidence,
                    "updated_at": datetime.now(UTC),
                },
                deep=True,
            )
            saved_session = self.assessments.save_session(advanced_session)

        return saved_session, scored_answer

    def _generate_question(
        self,
        *,
        goal: LearningGoalDTO,
        target_concepts: list[str],
        prior_answers: list[AssessmentAnswerDTO],
    ) -> AssessmentAgentOutput:
        payload = AssessmentAgentInput(
            goal_text=goal.goal_text,
            learner_profile=goal.learner_profile,
            prior_answers=prior_answers,
            target_concepts=target_concepts,
            current_confidence=0.0,
            question_count=len(prior_answers),
        )
        return validate_agent_output(
            agent_name=self.agent.agent_name,
            schema=AssessmentAgentOutput,
            payload=self.agent.generate_question(payload),
        )

    def _persist_answer(self, answer: AssessmentAnswerDTO) -> AssessmentAnswerDTO:
        score_output = validate_agent_output(
            agent_name=self.agent.agent_name,
            schema=AssessmentScoreOutput,
            payload=self.agent.score_answer(answer),
        )
        answer_to_save = build_scored_answer(answer, score_output)
        return create_or_get(
            create=self.assessments.create_answer,
            get=self.assessments.get_answer_by_id,
            record=answer_to_save,
            record_id=answer_to_save.answer_id,
        )


def build_started_session(
    *,
    goal: LearningGoalDTO,
    question: AssessmentQuestionDTO,
) -> AssessmentSessionDTO:
    now = datetime.now(UTC)
    return AssessmentSessionDTO(
        assessment_session_id=f"assessment_{uuid4().hex}",
        goal_id=goal.goal_id,
        run_id=goal.run_id,
        status=AssessmentStatus.IN_PROGRESS,
        question_count=0,
        confidence=0.0,
        concept_evidence=[],
        current_question=question,
        started_at=now,
        completed_at=None,
        termination_reason=None,
        created_at=now,
        updated_at=now,
    )


def build_pending_answer(
    *,
    goal: LearningGoalDTO,
    session: AssessmentSessionDTO,
    question: AssessmentQuestionDTO,
    answer_create: AssessmentAnswerCreate,
) -> AssessmentAnswerDTO:
    now = datetime.now(UTC)
    return AssessmentAnswerDTO(
        answer_id=f"answer_{uuid4().hex}",
        assessment_session_id=session.assessment_session_id,
        goal_id=goal.goal_id,
        question=question,
        answer_text=answer_create.answer_text,
        selected_options=answer_create.selected_options,
        self_rating=answer_create.self_rating,
        score=0.0,
        concept_scores=[],
        feedback=None,
        created_at=now,
        updated_at=now,
    )


def build_live_completed_session(
    *,
    session: AssessmentSessionDTO,
    answers: list[AssessmentAnswerDTO],
    evidence: list[ConceptEvidence],
    confidence: float,
) -> AssessmentSessionDTO:
    now = datetime.now(UTC)
    return session.model_copy(
        update={
            "status": AssessmentStatus.COMPLETED,
            "question_count": len(answers),
            "confidence": confidence,
            "concept_evidence": evidence,
            "current_question": None,
            "completed_at": now,
            "updated_at": now,
            "termination_reason": (
                "confidence_target_met"
                if confidence >= 0.75
                else "deterministic_question_limit_reached"
            ),
        },
        deep=True,
    )

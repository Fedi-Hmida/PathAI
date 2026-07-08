from __future__ import annotations

from dataclasses import dataclass

from app.agents.contracts import AssessorAgent
from app.agents.deterministic.assessment import (
    build_completed_session,
    build_scored_answer,
    diagnostic_focus_for_goal,
    seeded_answer_for_question,
)
from app.agents.services.common import create_or_get, validate_agent_output
from app.schemas.assessment import (
    AssessmentAgentInput,
    AssessmentAgentOutput,
    AssessmentAnswerDTO,
    AssessmentScoreOutput,
    AssessmentSessionDTO,
)
from app.schemas.goal import LearningGoalDTO
from app.services import AssessmentService


@dataclass(slots=True)
class AssessmentAgentService:
    agent: AssessorAgent
    assessments: AssessmentService

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

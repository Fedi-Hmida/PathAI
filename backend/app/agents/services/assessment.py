from __future__ import annotations

from dataclasses import dataclass

from app.agents.contracts import AssessorAgent
from app.agents.services.common import create_or_get, validate_agent_output
from app.fixtures import canonical_demo as demo
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
        payload = AssessmentAgentInput(
            goal_text=goal.goal_text,
            learner_profile=goal.learner_profile,
            prior_answers=[],
            target_concepts=[
                "rag_fundamentals",
                "retrieval_evaluation",
                "vector_search",
            ],
            current_confidence=0.0,
            question_count=0,
        )
        question_output = validate_agent_output(
            agent_name=self.agent.agent_name,
            schema=AssessmentAgentOutput,
            payload=self.agent.generate_question(payload),
        )
        session = demo.ASSESSMENT_SESSION.model_copy(
            update={"goal_id": goal.goal_id, "run_id": goal.run_id},
            deep=True,
        )
        saved_session = create_or_get(
            create=self.assessments.create_session,
            get=self.assessments.get_session_by_id,
            record=session,
            record_id=session.assessment_session_id,
        )
        for answer in demo.ASSESSMENT_ANSWERS:
            self._persist_answer(answer, question_output)
        return saved_session

    def _persist_answer(
        self,
        answer: AssessmentAnswerDTO,
        question_output: AssessmentAgentOutput,
    ) -> AssessmentAnswerDTO:
        score_output = validate_agent_output(
            agent_name=self.agent.agent_name,
            schema=AssessmentScoreOutput,
            payload=self.agent.score_answer(answer),
        )
        update: dict[str, object] = {}
        if answer.question.question_id == question_output.question.question_id:
            update["question"] = question_output.question
        if score_output.answer_id == answer.answer_id:
            update.update(
                {
                    "score": score_output.score,
                    "concept_scores": score_output.concept_scores,
                    "feedback": score_output.feedback,
                },
            )
        answer_to_save = answer.model_copy(update=update, deep=True)
        return create_or_get(
            create=self.assessments.create_answer,
            get=self.assessments.get_answer_by_id,
            record=answer_to_save,
            record_id=answer_to_save.answer_id,
        )

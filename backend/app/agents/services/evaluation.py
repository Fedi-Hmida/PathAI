from __future__ import annotations

from dataclasses import dataclass

from app.agents.contracts import EvaluationAgent
from app.agents.deterministic.evaluation import EVALUATION_WEIGHTS
from app.agents.services.common import create_or_get, validate_agent_output
from app.fixtures import canonical_demo as demo
from app.schemas.adaptation import AdaptationEventDTO
from app.schemas.assessment import AssessmentSessionDTO
from app.schemas.critic import CriticReviewDTO
from app.schemas.curriculum import CurriculumDTO
from app.schemas.evaluation import EvaluationAgentInput, EvaluationAgentOutput, EvaluationReportDTO
from app.schemas.goal import LearningGoalDTO
from app.schemas.knowledge_map import KnowledgeMapDTO
from app.schemas.quiz import QuizAttemptDTO
from app.schemas.resource import ResourceAttachmentDTO
from app.services import EvaluationService


@dataclass(slots=True)
class EvaluationAgentService:
    agent: EvaluationAgent
    evaluations: EvaluationService

    def evaluate(
        self,
        goal: LearningGoalDTO,
        assessment: AssessmentSessionDTO,
        knowledge_map: KnowledgeMapDTO,
        curriculum: CurriculumDTO,
        resources: list[ResourceAttachmentDTO],
        critic_review: CriticReviewDTO | None,
        quiz_attempt: QuizAttemptDTO | None,
        adaptation_event: AdaptationEventDTO | None,
    ) -> EvaluationReportDTO:
        payload = EvaluationAgentInput(
            goal=goal,
            assessment=assessment,
            knowledge_map=knowledge_map,
            curriculum=curriculum,
            resources=resources,
            critic_review=critic_review,
            quiz_attempt=quiz_attempt,
            adaptation_event=adaptation_event,
        )
        output = validate_agent_output(
            agent_name=self.agent.agent_name,
            schema=EvaluationAgentOutput,
            payload=self.agent.evaluate_run(payload),
        )
        report = EvaluationReportDTO(
            evaluation_report_id=demo.EVALUATION_REPORT_ID,
            goal_id=goal.goal_id,
            run_id=goal.run_id,
            metric_scores=output.metric_scores,
            weights=EVALUATION_WEIGHTS,
            overall_score=output.weighted_score,
            pass_status=output.pass_status,
            warnings=output.warnings,
            recommendations=output.recommendations,
            artifact_ids=_artifact_ids(
                goal=goal,
                assessment=assessment,
                knowledge_map=knowledge_map,
                curriculum=curriculum,
                critic_review=critic_review,
                quiz_attempt=quiz_attempt,
                adaptation_event=adaptation_event,
            ),
            created_at=demo.NOW,
            updated_at=demo.NOW,
        )
        return create_or_get(
            create=self.evaluations.create,
            get=self.evaluations.get_by_id,
            record=report,
            record_id=report.evaluation_report_id,
        )


def _artifact_ids(
    *,
    goal: LearningGoalDTO,
    assessment: AssessmentSessionDTO,
    knowledge_map: KnowledgeMapDTO,
    curriculum: CurriculumDTO,
    critic_review: CriticReviewDTO | None,
    quiz_attempt: QuizAttemptDTO | None,
    adaptation_event: AdaptationEventDTO | None,
) -> dict[str, str]:
    artifact_ids = {
        "goal_id": goal.goal_id,
        "assessment_session_id": assessment.assessment_session_id,
        "knowledge_map_id": knowledge_map.knowledge_map_id,
        "curriculum_id": curriculum.curriculum_id,
    }
    if critic_review is not None:
        artifact_ids["critic_review_id"] = critic_review.critic_review_id
    if quiz_attempt is not None:
        artifact_ids["quiz_attempt_id"] = quiz_attempt.quiz_attempt_id
    if adaptation_event is not None:
        artifact_ids["adaptation_event_id"] = adaptation_event.adaptation_event_id
    return artifact_ids

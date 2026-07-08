from __future__ import annotations

from app.agents.mock import MockEvaluationAgent
from app.agents.services.evaluation import EvaluationAgentService
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.schemas.evaluation import EvaluationAgentInput, EvaluationAgentOutput


def test_evaluation_agent_calculates_metrics_from_artifacts() -> None:
    output = MockEvaluationAgent().evaluate_run(_evaluation_input())

    assert EvaluationAgentOutput.model_validate(output) == output
    assert output.metric_scores.workflow_completeness == 1.0
    assert output.metric_scores.resource_diversity == 0.4
    assert output.metric_scores.resource_relevance == 0.93
    assert output.metric_scores.quiz_alignment >= 0.75
    assert output.metric_scores.adaptation_usefulness is not None
    assert output.weighted_score >= 0.7
    assert "Resource diversity" in " ".join(output.warnings)


def test_evaluation_agent_service_persists_calculated_report() -> None:
    container = ApiServiceContainer()
    service = EvaluationAgentService(MockEvaluationAgent(), container.evaluation_service)

    report = service.evaluate(
        demo.LEARNING_GOAL,
        demo.ASSESSMENT_SESSION,
        demo.KNOWLEDGE_MAP,
        demo.CURRICULUM,
        demo.RESOURCE_ATTACHMENTS,
        demo.CRITIC_REVIEW,
        demo.QUIZ_ATTEMPT,
        demo.ADAPTATION_EVENT,
    )

    stored = container.evaluation_service.get_by_id(report.evaluation_report_id)
    assert stored == report
    assert report.artifact_ids["goal_id"] == demo.GOAL_ID
    assert report.artifact_ids["quiz_attempt_id"] == demo.QUIZ_ATTEMPT_ID
    assert report.weights["workflow_completeness"] > 0
    assert report.overall_score == report.model_copy().overall_score


def _evaluation_input() -> EvaluationAgentInput:
    return EvaluationAgentInput(
        goal=demo.LEARNING_GOAL,
        assessment=demo.ASSESSMENT_SESSION,
        knowledge_map=demo.KNOWLEDGE_MAP,
        curriculum=demo.CURRICULUM,
        resources=demo.RESOURCE_ATTACHMENTS,
        critic_review=demo.CRITIC_REVIEW,
        quiz_attempt=demo.QUIZ_ATTEMPT,
        adaptation_event=demo.ADAPTATION_EVENT,
    )

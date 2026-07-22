from __future__ import annotations

from app.agents.services import build_mock_agent_service_bundle
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo


def test_agent_services_call_mocks_and_persist_through_domain_services() -> None:
    container = ApiServiceContainer()
    agents = build_mock_agent_service_bundle(
        goals=container.goal_service,
        assessments=container.assessment_service,
        knowledge_maps=container.knowledge_map_service,
        curricula=container.curriculum_service,
        resources=container.resource_service,
        critics=container.critic_service,
        progress=container.progress_service,
        quizzes=container.quiz_service,
        adaptations=container.adaptation_service,
        evaluations=container.evaluation_service,
    )

    goal = container.goal_service.create(demo.LEARNING_GOAL)
    assessment = agents.assessment.run_diagnostic(goal)
    answers = container.assessment_service.list_answers_by_session_id(
        assessment.assessment_session_id,
    )
    knowledge_map = agents.knowledge_map.build(goal, assessment, answers)
    curriculum = agents.curriculum.build(goal, knowledge_map)
    attachments = agents.resource.attach(curriculum, knowledge_map)
    critic = agents.critic.review(goal, knowledge_map, curriculum, attachments)
    progress = agents.progress.build(goal, curriculum)
    quiz, attempt = agents.quiz.build(goal, curriculum, progress)
    adaptation = agents.adaptation.plan(goal, curriculum, progress, attempt)
    evaluation = agents.evaluation.evaluate(
        goal,
        assessment,
        knowledge_map,
        curriculum,
        attachments,
        critic,
        attempt,
        adaptation,
    )

    assert container.knowledge_map_service.get_by_id(demo.KNOWLEDGE_MAP_ID) == knowledge_map
    assert container.curriculum_service.get_by_id(demo.CURRICULUM_ID) == curriculum
    assert container.resource_service.list_attachments_by_curriculum_id(
        demo.CURRICULUM_ID,
    ) == attachments
    assert container.critic_service.get_by_id(demo.CRITIC_REVIEW_ID) == critic
    assert container.progress_service.get_by_id(demo.PROGRESS_ID) == progress
    assert container.quiz_service.get_quiz_by_id(demo.QUIZ_ID) == quiz
    assert container.quiz_service.get_attempt_by_id(demo.QUIZ_ATTEMPT_ID) == attempt
    assert container.adaptation_service.get_by_id(demo.ADAPTATION_ID) == adaptation
    assert container.evaluation_service.get_by_id(demo.EVALUATION_REPORT_ID) == evaluation

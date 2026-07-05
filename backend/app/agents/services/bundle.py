from __future__ import annotations

from dataclasses import dataclass

from app.agents.mock import (
    MockAdapterAgent,
    MockAssessorAgent,
    MockCriticAgent,
    MockCurriculumAgent,
    MockEvaluationAgent,
    MockKnowledgeMapAgent,
    MockProgressAgent,
    MockQuizAgent,
    MockResourceAgent,
)
from app.agents.services.adaptation import AdaptationAgentService
from app.agents.services.assessment import AssessmentAgentService
from app.agents.services.critic import CriticAgentService
from app.agents.services.curriculum import CurriculumAgentService
from app.agents.services.evaluation import EvaluationAgentService
from app.agents.services.knowledge_map import KnowledgeMapAgentService
from app.agents.services.progress import ProgressAgentService
from app.agents.services.quiz import QuizAgentService
from app.agents.services.resource import ResourceAgentService
from app.services import (
    AdaptationService,
    AssessmentService,
    CriticService,
    CurriculumService,
    EvaluationService,
    KnowledgeMapService,
    ProgressService,
    QuizService,
    ResourceService,
)


@dataclass(slots=True)
class AgentServiceBundle:
    assessment: AssessmentAgentService
    knowledge_map: KnowledgeMapAgentService
    curriculum: CurriculumAgentService
    resource: ResourceAgentService
    critic: CriticAgentService
    progress: ProgressAgentService
    quiz: QuizAgentService
    adaptation: AdaptationAgentService
    evaluation: EvaluationAgentService


def build_mock_agent_service_bundle(
    *,
    assessments: AssessmentService,
    knowledge_maps: KnowledgeMapService,
    curricula: CurriculumService,
    resources: ResourceService,
    critics: CriticService,
    progress: ProgressService,
    quizzes: QuizService,
    adaptations: AdaptationService,
    evaluations: EvaluationService,
) -> AgentServiceBundle:
    return AgentServiceBundle(
        assessment=AssessmentAgentService(MockAssessorAgent(), assessments),
        knowledge_map=KnowledgeMapAgentService(MockKnowledgeMapAgent(), knowledge_maps),
        curriculum=CurriculumAgentService(MockCurriculumAgent(), curricula),
        resource=ResourceAgentService(MockResourceAgent(), resources),
        critic=CriticAgentService(MockCriticAgent(), critics),
        progress=ProgressAgentService(MockProgressAgent(), progress),
        quiz=QuizAgentService(MockQuizAgent(), quizzes),
        adaptation=AdaptationAgentService(MockAdapterAgent(), adaptations),
        evaluation=EvaluationAgentService(MockEvaluationAgent(), evaluations),
    )

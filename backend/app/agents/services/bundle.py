from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.agents.contracts import AssessorAgent, CriticAgent, CurriculumAgent, KnowledgeMapAgent
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


class AssessmentAgentMode(StrEnum):
    DETERMINISTIC = "deterministic"
    LLM = "llm"


class KnowledgeMapAgentMode(StrEnum):
    DETERMINISTIC = "deterministic"
    LLM = "llm"


class CriticAgentMode(StrEnum):
    DETERMINISTIC = "deterministic"
    LLM = "llm"


class CurriculumAgentMode(StrEnum):
    DETERMINISTIC = "deterministic"
    LLM = "llm"


@dataclass(frozen=True, slots=True)
class AgentIntegrationSwitches:
    assessment_agent_mode: AssessmentAgentMode = AssessmentAgentMode.DETERMINISTIC
    knowledge_map_agent_mode: KnowledgeMapAgentMode = KnowledgeMapAgentMode.DETERMINISTIC
    critic_agent_mode: CriticAgentMode = CriticAgentMode.DETERMINISTIC
    curriculum_agent_mode: CurriculumAgentMode = CurriculumAgentMode.DETERMINISTIC


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
    switches: AgentIntegrationSwitches | None = None,
    assessment_agent: AssessorAgent | None = None,
    knowledge_map_agent: KnowledgeMapAgent | None = None,
    critic_agent: CriticAgent | None = None,
    curriculum_agent: CurriculumAgent | None = None,
) -> AgentServiceBundle:
    selected_switches = switches or AgentIntegrationSwitches()
    return AgentServiceBundle(
        assessment=AssessmentAgentService(
            _select_assessment_agent(selected_switches, assessment_agent),
            assessments,
        ),
        knowledge_map=KnowledgeMapAgentService(
            _select_knowledge_map_agent(selected_switches, knowledge_map_agent),
            knowledge_maps,
        ),
        curriculum=CurriculumAgentService(
            _select_curriculum_agent(selected_switches, curriculum_agent),
            curricula,
        ),
        resource=ResourceAgentService(MockResourceAgent(), resources),
        critic=CriticAgentService(
            _select_critic_agent(selected_switches, critic_agent),
            critics,
        ),
        progress=ProgressAgentService(MockProgressAgent(), progress),
        quiz=QuizAgentService(MockQuizAgent(), quizzes),
        adaptation=AdaptationAgentService(MockAdapterAgent(), adaptations),
        evaluation=EvaluationAgentService(MockEvaluationAgent(), evaluations),
    )


def _select_assessment_agent(
    switches: AgentIntegrationSwitches,
    injected_agent: AssessorAgent | None,
) -> AssessorAgent:
    if switches.assessment_agent_mode == AssessmentAgentMode.LLM:
        if injected_agent is None:
            msg = "LLM assessment mode requires an injected assessment agent."
            raise ValueError(msg)
        return injected_agent
    return injected_agent or MockAssessorAgent()


def _select_knowledge_map_agent(
    switches: AgentIntegrationSwitches,
    injected_agent: KnowledgeMapAgent | None,
) -> KnowledgeMapAgent:
    if switches.knowledge_map_agent_mode == KnowledgeMapAgentMode.LLM:
        if injected_agent is None:
            msg = "LLM knowledge-map mode requires an injected knowledge-map agent."
            raise ValueError(msg)
        return injected_agent
    return injected_agent or MockKnowledgeMapAgent()


def _select_critic_agent(
    switches: AgentIntegrationSwitches,
    injected_agent: CriticAgent | None,
) -> CriticAgent:
    if switches.critic_agent_mode == CriticAgentMode.LLM:
        if injected_agent is None:
            msg = "LLM critic mode requires an injected critic agent."
            raise ValueError(msg)
        return injected_agent
    return injected_agent or MockCriticAgent()


def _select_curriculum_agent(
    switches: AgentIntegrationSwitches,
    injected_agent: CurriculumAgent | None,
) -> CurriculumAgent:
    if switches.curriculum_agent_mode == CurriculumAgentMode.LLM:
        if injected_agent is None:
            msg = "LLM curriculum mode requires an injected curriculum agent."
            raise ValueError(msg)
        return injected_agent
    return injected_agent or MockCurriculumAgent()

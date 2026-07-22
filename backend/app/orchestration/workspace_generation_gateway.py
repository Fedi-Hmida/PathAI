"""The one sanctioned seam through which the API layer reaches agent-backed
per-user knowledge-map/curriculum regeneration.

`app/api/v1/*` must never import `app.agents` directly (enforced by
`test_api_scope_security.py`), and `app/services/*` must never import
`app.agents`/`app.orchestration` at all (enforced by
`test_repository_scope_security.py`). This module lives under
`app/orchestration/` for the same reason `assessment_agent_gateway.py` does -
it is the sanctioned crossing point `app/api/v1/dependencies.py` uses.

It reuses the exact same construction `assessment_agent_gateway.py` and
`app/orchestration/nodes.py`'s `_build_default_agent_service_bundle` already
do (`resolve_agent_integration_switches` -> `build_injected_agents` ->
`build_mock_agent_service_bundle`), so `PATHAI_ENABLE_LLM_KNOWLEDGE_MAP_AGENT`
/ `PATHAI_ENABLE_LLM_CURRICULUM_AGENT` take effect here too.
"""

from __future__ import annotations

from app.agents.services import (
    AssessmentNotCompleteError as AssessmentNotCompleteError,
)
from app.agents.services import build_mock_agent_service_bundle
from app.agents.services.activation import build_injected_agents, resolve_agent_integration_switches
from app.agents.services.workspace_generation import (
    WorkspaceGenerationService as WorkspaceGenerationService,
)
from app.core.settings import Settings
from app.orchestration.nodes import ServiceContainerProtocol


def build_workspace_generation_service(
    container: ServiceContainerProtocol,
    settings: Settings,
) -> WorkspaceGenerationService:
    switches = resolve_agent_integration_switches(settings)
    injected = build_injected_agents(switches, settings)
    bundle = build_mock_agent_service_bundle(
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
        switches=switches,
        assessment_agent=injected.assessment,
        knowledge_map_agent=injected.knowledge_map,
        critic_agent=injected.critic,
        curriculum_agent=injected.curriculum,
    )
    return WorkspaceGenerationService(
        knowledge_map_agent=bundle.knowledge_map,
        curriculum_agent=bundle.curriculum,
        critic_agent=bundle.critic,
        evaluation_agent=bundle.evaluation,
        quiz_agent=bundle.quiz,
        progress_agent=bundle.progress,
        assessments=container.assessment_service,
        knowledge_maps=container.knowledge_map_service,
        curricula=container.curriculum_service,
        critics=container.critic_service,
        evaluations=container.evaluation_service,
        quizzes=container.quiz_service,
        progress=container.progress_service,
        goals=container.goal_service,
        llm_observer=injected.observer,
    )

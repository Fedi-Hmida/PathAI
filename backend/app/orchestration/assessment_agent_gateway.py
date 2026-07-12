"""The one sanctioned seam through which the API layer reaches agent-backed
assessment behavior.

`app/api/v1/*` must never import `app.agents` directly (enforced by
`test_api_scope_security.py`), and `app/services/*` must never import
`app.agents`/`app.orchestration` at all (enforced by
`test_repository_scope_security.py`). This module lives under
`app/orchestration/` — already the sanctioned crossing point
`app/api/v1/dependencies.py` uses for the demo pipeline (`runner.py`) — and
re-exports exactly what `app/api/v1/dependencies.py` and `app/api/v1/errors.py`
need.

It reuses the exact same construction `app/orchestration/nodes.py`'s
`_build_default_agent_service_bundle` already does for the orchestration graph
(`resolve_agent_integration_switches` -> `build_injected_agents` ->
`build_mock_agent_service_bundle`), so a `PATHAI_ENABLE_LLM_ASSESSMENT_AGENT`
flag takes effect here too, and never constructs a mock agent instance or
touches an agent contract type directly (forbidden for files under this
package, per `test_agent_scope_security.py`).
"""

from __future__ import annotations

from app.agents.errors import AgentError as AgentError
from app.agents.services import build_mock_agent_service_bundle
from app.agents.services.activation import build_injected_agents, resolve_agent_integration_switches
from app.agents.services.assessment import AssessmentAgentService as AssessmentAgentService
from app.agents.services.assessment import (
    AssessmentQuestionMismatchError as AssessmentQuestionMismatchError,
)
from app.agents.services.assessment import (
    AssessmentSessionNotActiveError as AssessmentSessionNotActiveError,
)
from app.core.settings import Settings
from app.orchestration.nodes import ServiceContainerProtocol


def build_assessment_agent_service(
    container: ServiceContainerProtocol,
    settings: Settings,
) -> AssessmentAgentService:
    switches = resolve_agent_integration_switches(settings)
    injected = build_injected_agents(switches, settings)
    return build_mock_agent_service_bundle(
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
    ).assessment

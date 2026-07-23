"""The sanctioned seam through which the API layer reaches the real
post-quiz-submission flow (Big_Audit Step 11): scoring a submitted attempt,
refreshing real Progress from it, and conditionally triggering a real
Adaptation event only when a genuine threshold is actually crossed.

Same justification as the other `*_gateway.py` modules under this package:
`app/api/v1/*` must never import `app.agents` directly (enforced by
`test_api_scope_security.py`). Quiz, progress, and adaptation all have no LLM
mode - each is always its deterministic default - so this gateway needs no
integration-switch resolution, unlike `assessment_agent_gateway.py` /
`workspace_generation_gateway.py`.
"""

from __future__ import annotations

from app.agents.services.adaptation import build_default_adaptation_agent_service
from app.agents.services.progress import build_default_progress_agent_service
from app.agents.services.quiz import build_default_quiz_agent_service
from app.agents.services.quiz_submission import QuizSubmissionService as QuizSubmissionService
from app.orchestration.nodes import ServiceContainerProtocol


def build_quiz_submission_service(
    container: ServiceContainerProtocol,
) -> QuizSubmissionService:
    return QuizSubmissionService(
        quiz_agent=build_default_quiz_agent_service(container.quiz_service),
        progress_agent=build_default_progress_agent_service(container.progress_service),
        adaptation_agent=build_default_adaptation_agent_service(container.adaptation_service),
        goals=container.goal_service,
        curricula=container.curriculum_service,
    )

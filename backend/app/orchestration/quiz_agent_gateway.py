"""The sanctioned seam through which the API layer reaches the agent-backed
real quiz-attempt submission path (Big_Audit Step 10).

Same justification as `assessment_agent_gateway.py` /
`workspace_generation_gateway.py`: `app/api/v1/*` must never import
`app.agents` directly (enforced by `test_api_scope_security.py`), so this
module lives under `app/orchestration/` as the crossing point
`app/api/v1/dependencies.py` uses. The quiz agent has no LLM mode (unlike
assessment/knowledge-map/critic/curriculum) - it is always the deterministic
default, so no integration-switch resolution is needed here. This module
must not reference the mock agent implementation package directly (enforced
by `test_agent_scope_security.py`), hence the indirection through
`build_default_quiz_agent_service` - the same way `bundle.py` keeps that
reference confined to the agent services layer.
"""

from __future__ import annotations

from app.agents.services.quiz import QuizAgentService as QuizAgentService
from app.agents.services.quiz import build_default_quiz_agent_service
from app.services import QuizService


def build_quiz_agent_service(quizzes: QuizService) -> QuizAgentService:
    return build_default_quiz_agent_service(quizzes)

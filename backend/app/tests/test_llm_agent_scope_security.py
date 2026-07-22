from __future__ import annotations

from pathlib import Path

from app.agents.deterministic.knowledge_map import build_knowledge_map_output
from app.agents.llm import LLMKnowledgeMapAgent
from app.agents.mock import MockKnowledgeMapAgent
from app.agents.services import (
    AgentIntegrationSwitches,
    KnowledgeMapAgentMode,
    build_mock_agent_service_bundle,
)
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.llm import FakeLLMClient
from app.orchestration.nodes import OrchestrationContext
from app.orchestration.runner import run_straight_line_demo
from app.orchestration.state import workflow_state_to_graph_state
from app.schemas.knowledge_map import KnowledgeMapAgentInput, KnowledgeMapAgentOutput

APP_DIR = Path(__file__).resolve().parents[1]
LLM_AGENT_DIR = APP_DIR / "agents" / "llm"


def test_only_llm_agent_package_imports_llm_adapter_from_agents() -> None:
    allowed = {path.resolve() for path in LLM_AGENT_DIR.rglob("*.py")}
    for path in (APP_DIR / "agents").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "app.llm" in text:
            assert path.resolve() in allowed, f"{path} imports app.llm outside llm agents"


def test_routes_repositories_and_orchestration_still_do_not_import_llm() -> None:
    for directory in (APP_DIR / "api", APP_DIR / "repositories", APP_DIR / "orchestration"):
        for path in directory.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert "app.llm" not in text, f"{path} imports app.llm"


def test_llm_agent_path_does_not_put_raw_llm_data_in_workflow_state() -> None:
    container = ApiServiceContainer()
    llm_agent = LLMKnowledgeMapAgent(
        client=_fake_knowledge_map_client(),
        fallback_agent=MockKnowledgeMapAgent(),
    )
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
        switches=AgentIntegrationSwitches(
            knowledge_map_agent_mode=KnowledgeMapAgentMode.LLM,
        ),
        knowledge_map_agent=llm_agent,
    )

    result = run_straight_line_demo(
        OrchestrationContext.from_container(container, agent_services=agents),
    )

    dumped_state = str(workflow_state_to_graph_state(result.state)).lower()
    assert "prompt" not in dumped_state
    assert "raw" not in dumped_state
    assert "provider" not in dumped_state
    assert "answer_key" not in dumped_state


def _fake_knowledge_map_client() -> FakeLLMClient:
    payload = build_knowledge_map_output(
        KnowledgeMapAgentInput(
            goal_text=demo.LEARNING_GOAL.goal_text,
            assessment_answers=demo.ASSESSMENT_ANSWERS,
            concept_evidence=demo.ASSESSMENT_SESSION.concept_evidence,
        ),
    )
    return FakeLLMClient(
        payloads={
            KnowledgeMapAgentOutput.__name__: payload.model_dump(mode="json"),
        },
    )

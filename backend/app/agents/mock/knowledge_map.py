from __future__ import annotations

from app.agents.mock.base import deterministic_output
from app.fixtures import mock_agents
from app.schemas.knowledge_map import KnowledgeMapAgentInput, KnowledgeMapAgentOutput


class MockKnowledgeMapAgent:
    agent_name = "knowledge_map"

    def __init__(self, *, fail: bool = False, malformed: bool = False) -> None:
        self._fail = fail
        self._malformed = malformed

    def build_knowledge_map(self, _payload: KnowledgeMapAgentInput) -> KnowledgeMapAgentOutput:
        return deterministic_output(
            agent_name=self.agent_name,
            output=mock_agents.KNOWLEDGE_MAP_AGENT_OUTPUT,
            fail=self._fail,
            malformed=self._malformed,
        )

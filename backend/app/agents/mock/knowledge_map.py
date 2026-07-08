from __future__ import annotations

from app.agents.deterministic.knowledge_map import build_knowledge_map_output
from app.agents.mock.base import deterministic_output
from app.schemas.knowledge_map import KnowledgeMapAgentInput, KnowledgeMapAgentOutput


class MockKnowledgeMapAgent:
    agent_name = "knowledge_map"

    def __init__(self, *, fail: bool = False, malformed: bool = False) -> None:
        self._fail = fail
        self._malformed = malformed

    def build_knowledge_map(self, payload: KnowledgeMapAgentInput) -> KnowledgeMapAgentOutput:
        return deterministic_output(
            agent_name=self.agent_name,
            output=build_knowledge_map_output(payload),
            fail=self._fail,
            malformed=self._malformed,
        )

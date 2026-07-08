from __future__ import annotations

import json
from collections.abc import Mapping
from enum import StrEnum

from pydantic import BaseModel

from app.llm.contracts import (
    RawLLMResponse,
    StructuredModel,
    StructuredOutputRequest,
)
from app.llm.errors import LLMProviderError, LLMTimeoutError
from app.llm.structured_output import parse_structured_output
from app.schemas.llm_spike import (
    MiniCurriculumOutput,
    MiniKnowledgeMapOutput,
    MiniQuizOutput,
)


class FakeLLMScenario(StrEnum):
    VALID_JSON = "valid_json"
    FENCED_JSON = "fenced_json"
    INVALID_JSON = "invalid_json"
    SCHEMA_INVALID_JSON = "schema_invalid_json"
    EMPTY = "empty"
    TIMEOUT = "timeout"
    PROVIDER_ERROR = "provider_error"


class FakeLLMClient:
    def __init__(
        self,
        *,
        scenario: FakeLLMScenario = FakeLLMScenario.VALID_JSON,
        provider: str = "fake",
        model: str = "deterministic-fake",
        payloads: Mapping[str, object] | None = None,
        scripted_responses: list[str] | None = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self.scenario = scenario
        self.payloads = dict(payloads or _default_payloads())
        self.scripted_responses = list(scripted_responses or [])
        self.call_count = 0

    async def generate(self, request: StructuredOutputRequest) -> RawLLMResponse:
        self.call_count += 1
        if self.scripted_responses:
            text = self.scripted_responses[
                min(self.call_count - 1, len(self.scripted_responses) - 1)
            ]
            return self._response(request, text)
        if self.scenario == FakeLLMScenario.TIMEOUT:
            raise LLMTimeoutError("Fake LLM timeout.", provider=self.provider)
        if self.scenario == FakeLLMScenario.PROVIDER_ERROR:
            raise LLMProviderError("Fake LLM provider error.", provider=self.provider)
        if self.scenario == FakeLLMScenario.EMPTY:
            return self._response(request, "")
        if self.scenario == FakeLLMScenario.INVALID_JSON:
            return self._response(request, "not valid JSON {")
        if self.scenario == FakeLLMScenario.SCHEMA_INVALID_JSON:
            return self._response(request, json.dumps({"unexpected": []}))

        payload = self.payloads.get(request.schema_name)
        if payload is None:
            raise LLMProviderError(
                f"No fake LLM payload for schema {request.schema_name}.",
                provider=self.provider,
                retryable=False,
            )
        text = json.dumps(payload)
        if self.scenario == FakeLLMScenario.FENCED_JSON:
            text = f"```json\n{text}\n```"
        return self._response(request, text)

    async def generate_structured(
        self,
        request: StructuredOutputRequest,
        output_schema: type[StructuredModel],
    ) -> StructuredModel:
        response = await self.generate(request)
        return parse_structured_output(response.text, output_schema)

    def _response(self, request: StructuredOutputRequest, text: str) -> RawLLMResponse:
        return RawLLMResponse(
            provider=self.provider,
            model=self.model,
            text=text,
            request_id=request.request_id,
            finish_reason="stop",
        )


def _default_payloads() -> dict[str, object]:
    return {
        MiniKnowledgeMapOutput.__name__: {
            "concepts": [
                {
                    "concept_id": "retrieval_evaluation",
                    "label": "Retrieval evaluation",
                    "mastery_score": 0.35,
                    "classification": "weak",
                }
            ],
            "summary": "The learner needs more practice with retrieval evaluation.",
        },
        MiniCurriculumOutput.__name__: {
            "title": "RAG Foundations Sprint",
            "weeks": [
                {
                    "week_number": 1,
                    "theme": "Retrieval basics",
                    "topics": ["RAG overview", "Retriever role"],
                }
            ],
        },
        MiniQuizOutput.__name__: {
            "questions": [
                {
                    "prompt": "What does recall@k measure?",
                    "options": [
                        "Relevant items retrieved in the top k",
                        "Response fluency",
                        "Prompt length",
                        "Frontend latency",
                    ],
                    "correct_answer": "Relevant items retrieved in the top k",
                    "concept_ids": ["retrieval_evaluation"],
                }
            ],
        },
    }


def fake_payload_for_schema(output_schema: type[BaseModel]) -> dict[str, object]:
    payload = _default_payloads().get(output_schema.__name__)
    if not isinstance(payload, dict):
        msg = f"No deterministic fake payload for schema {output_schema.__name__}"
        raise ValueError(msg)
    return payload

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from app.agents.contracts import KnowledgeMapAgent
from app.agents.errors import LLMGenerationUnavailableError
from app.llm.contracts import (
    LLMClient,
    LLMModelMetadata,
    LLMRetryPolicy,
    LLMTimeoutPolicy,
    StructuredOutputRequest,
)
from app.llm.errors import LLMError, LLMProviderError
from app.llm.observability.events import LLMReliabilityEvent, LLMReliabilityEventType
from app.llm.observability.observer import LLMReliabilityObserver, NullObserver
from app.llm.retry import generate_structured_with_retry
from app.schemas.assessment import AssessmentAnswerDTO, ConceptEvidence
from app.schemas.knowledge_map import KnowledgeMapAgentInput, KnowledgeMapAgentOutput


@dataclass(slots=True)
class LLMKnowledgeMapAgent:
    client: LLMClient
    fallback_agent: KnowledgeMapAgent | None = None
    fallback_on_error: bool = True
    retry_policy: LLMRetryPolicy = field(default_factory=LLMRetryPolicy)
    timeout_policy: LLMTimeoutPolicy = field(default_factory=LLMTimeoutPolicy)
    max_output_tokens: int = 2048

    agent_name: str = "knowledge_map_llm"
    observer: LLMReliabilityObserver = field(default_factory=NullObserver)

    def build_knowledge_map(self, payload: KnowledgeMapAgentInput) -> KnowledgeMapAgentOutput:
        request = StructuredOutputRequest(
            prompt=_build_schema_focused_prompt(payload),
            schema_name=KnowledgeMapAgentOutput.__name__,
            request_id="knowledge_map_llm_agent",
            metadata=LLMModelMetadata(provider="adapter", model="knowledge-map-agent"),
            timeout=self.timeout_policy,
            max_output_tokens=self.max_output_tokens,
            temperature=0.0,
        )
        try:
            return _run_structured_sync(
                self.client,
                request,
                self.retry_policy,
                self.observer,
            )
        except LLMError as exc:
            if self.fallback_on_error and self.fallback_agent is not None:
                self.observer.record(
                    LLMReliabilityEvent(
                        event_type=LLMReliabilityEventType.FALLBACK_USED,
                        schema_name=KnowledgeMapAgentOutput.__name__,
                        attempt=self.retry_policy.max_attempts,
                        max_attempts=self.retry_policy.max_attempts,
                        error_code=exc.error_code,
                        reason_code="fallback_to_deterministic",
                    ),
                )
                return self.fallback_agent.build_knowledge_map(payload)
            self.observer.record(
                LLMReliabilityEvent(
                    event_type=LLMReliabilityEventType.GENERATION_UNAVAILABLE,
                    schema_name=KnowledgeMapAgentOutput.__name__,
                    attempt=self.retry_policy.max_attempts,
                    max_attempts=self.retry_policy.max_attempts,
                    error_code=exc.error_code,
                    reason_code="fail_loud_no_fallback",
                ),
            )
            raise LLMGenerationUnavailableError(self.agent_name) from exc


def _run_structured_sync(
    client: LLMClient,
    request: StructuredOutputRequest,
    retry_policy: LLMRetryPolicy,
    observer: LLMReliabilityObserver,
) -> KnowledgeMapAgentOutput:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(
            generate_structured_with_retry(
                client,
                request,
                KnowledgeMapAgentOutput,
                policy=retry_policy,
                observer=observer,
            ),
        )
    raise LLMProviderError(
        "LLM knowledge-map agent requires the sync service boundary to run outside "
        "an active event loop.",
        provider="adapter",
        retryable=False,
    )


def _build_schema_focused_prompt(payload: KnowledgeMapAgentInput) -> str:
    evidence = "\n".join(_concept_evidence_line(item) for item in payload.concept_evidence)
    answers = "\n".join(_answer_line(answer) for answer in payload.assessment_answers)
    if not answers:
        answers = "- no assessment answers were provided"

    return (
        "You are PathAI's knowledge-map transformation component. "
        "Return strict JSON only for KnowledgeMapAgentOutput. "
        "Do not include markdown, commentary, secrets, provider metadata, or raw prompts.\n\n"
        f"Goal: {_bounded(payload.goal_text, 500)}\n\n"
        "Concept evidence:\n"
        f"{evidence}\n\n"
        "Assessment answer signals:\n"
        f"{answers}\n\n"
        "Required JSON fields: concepts, strong_concepts, developing_concepts, "
        "weak_concepts, missing_concepts, confidence, summary. "
        "Each concept must include concept_id, label, mastery_score, classification, "
        "evidence, prerequisites, recommended_action, and confidence. "
        "The evidence and prerequisites fields must each be a JSON array of short strings "
        "(never a single string, even if there is only one item). "
        "strong_concepts, developing_concepts, weak_concepts, and missing_concepts must "
        "each be a JSON array containing only the concept_id string values from concepts "
        "above, grouped by classification — never full concept objects.\n"
        "Strict value rules (output is rejected otherwise):\n"
        "- concept_id and every prerequisites entry: lowercase snake_case matching "
        "^[a-z][a-z0-9_]+$, e.g. 'linear_algebra' (never 'Linear Algebra' or a display label).\n"
        "- classification: exactly one of 'strong', 'developing', 'weak', 'missing'.\n"
        "- mastery_score and confidence: numbers between 0.0 and 1.0."
    )


def _concept_evidence_line(item: ConceptEvidence) -> str:
    evidence = "; ".join(_bounded(value, 120) for value in item.evidence) or "no notes"
    return f"- {item.concept_id}: score={item.score:.2f}; evidence={evidence}"


def _answer_line(answer: AssessmentAnswerDTO) -> str:
    concepts = ", ".join(answer.question.target_concepts) or "none"
    return (
        f"- question={answer.question.question_id}; concepts={concepts}; "
        f"score={answer.score:.2f}"
    )


def _bounded(value: str, max_length: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[: max_length - 3]}..."

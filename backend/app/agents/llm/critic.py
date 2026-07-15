from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from app.agents.contracts import CriticAgent
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
from app.schemas.critic import CriticAgentInput, CriticAgentOutput
from app.schemas.curriculum import CurriculumDTO
from app.schemas.resource import ResourceAttachmentDTO


@dataclass(slots=True)
class LLMCriticAgent:
    client: LLMClient
    fallback_agent: CriticAgent | None = None
    fallback_on_error: bool = True
    retry_policy: LLMRetryPolicy = field(default_factory=LLMRetryPolicy)
    timeout_policy: LLMTimeoutPolicy = field(default_factory=LLMTimeoutPolicy)
    max_output_tokens: int = 2048

    agent_name: str = "critic_llm"
    observer: LLMReliabilityObserver = field(default_factory=NullObserver)

    def review_curriculum(self, payload: CriticAgentInput) -> CriticAgentOutput:
        request = StructuredOutputRequest(
            prompt=_build_schema_focused_prompt(payload),
            schema_name=CriticAgentOutput.__name__,
            request_id="critic_llm_agent",
            metadata=LLMModelMetadata(provider="adapter", model="critic-agent"),
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
                        schema_name=CriticAgentOutput.__name__,
                        attempt=self.retry_policy.max_attempts,
                        max_attempts=self.retry_policy.max_attempts,
                        error_code=exc.error_code,
                        reason_code="fallback_to_deterministic",
                    ),
                )
                return self.fallback_agent.review_curriculum(payload)
            self.observer.record(
                LLMReliabilityEvent(
                    event_type=LLMReliabilityEventType.GENERATION_UNAVAILABLE,
                    schema_name=CriticAgentOutput.__name__,
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
) -> CriticAgentOutput:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(
            generate_structured_with_retry(
                client,
                request,
                CriticAgentOutput,
                policy=retry_policy,
                observer=observer,
            ),
        )
    raise LLMProviderError(
        "LLM critic agent requires the sync service boundary to run outside an active event loop.",
        provider="adapter",
        retryable=False,
    )


def _build_schema_focused_prompt(payload: CriticAgentInput) -> str:
    attachments = "\n".join(_attachment_line(item) for item in payload.resource_attachments)
    if not attachments:
        attachments = "- no resource attachments were provided"

    return (
        "You are PathAI's critic transformation component. "
        "Return strict JSON only for CriticAgentOutput. "
        "Do not include markdown, commentary, secrets, provider metadata, or raw prompts.\n\n"
        f"Goal: {_bounded(payload.goal_text, 500)}\n\n"
        f"Knowledge map summary: {_bounded(payload.knowledge_map.summary, 500)}\n\n"
        f"Curriculum title: {_bounded(payload.curriculum.title, 220)}; "
        f"weeks={len(payload.curriculum.weeks)}; "
        f"topics={_curriculum_topic_count(payload.curriculum)}\n\n"
        "Resource attachments:\n"
        f"{attachments}\n\n"
        "Required JSON fields: overall_score, pass_status, dimension_scores, strengths, issues, "
        "revision_recommendations. "
        "dimension_scores must include coverage, pacing, resource_relevance, assessment_alignment, "
        "and quiz_readiness."
    )


def _attachment_line(item: ResourceAttachmentDTO) -> str:
    return (
        f"- attachment={item.attachment_id}; topic={item.topic_id}; "
        f"rank={item.rank}; relevance={item.relevance_score:.2f}; "
        f"reason={_bounded(item.selection_reason, 140)}"
    )


def _curriculum_topic_count(curriculum: CurriculumDTO) -> int:
    topic_count = 0
    for week in curriculum.weeks:
        topic_count += len(week.topics)
    return topic_count


def _bounded(value: str, max_length: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[: max_length - 3]}..."
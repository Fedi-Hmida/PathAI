from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from app.agents.contracts import CurriculumAgent
from app.agents.errors import AgentError
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
from app.schemas.curriculum import CurriculumAgentInput, CurriculumAgentOutput
from app.schemas.knowledge_map import ConceptMasteryDTO


@dataclass(slots=True)
class LLMCurriculumAgent:
    client: LLMClient
    fallback_agent: CurriculumAgent | None = None
    fallback_on_error: bool = True
    retry_policy: LLMRetryPolicy = field(default_factory=LLMRetryPolicy)
    timeout_policy: LLMTimeoutPolicy = field(default_factory=LLMTimeoutPolicy)
    max_output_tokens: int = 2048

    agent_name: str = "curriculum_llm"
    observer: LLMReliabilityObserver = field(default_factory=NullObserver)

    def build_curriculum(self, payload: CurriculumAgentInput) -> CurriculumAgentOutput:
        request = StructuredOutputRequest(
            prompt=_build_schema_focused_prompt(payload),
            schema_name=CurriculumAgentOutput.__name__,
            request_id="curriculum_llm_agent",
            metadata=LLMModelMetadata(provider="adapter", model="curriculum-agent"),
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
                        schema_name=CurriculumAgentOutput.__name__,
                        attempt=self.retry_policy.max_attempts,
                        max_attempts=self.retry_policy.max_attempts,
                        error_code=exc.error_code,
                        reason_code="fallback_to_deterministic",
                    ),
                )
                return self.fallback_agent.build_curriculum(payload)
            raise AgentError(
                self.agent_name,
                "LLM-backed curriculum generation failed safely.",
            ) from exc


def _run_structured_sync(
    client: LLMClient,
    request: StructuredOutputRequest,
    retry_policy: LLMRetryPolicy,
    observer: LLMReliabilityObserver,
) -> CurriculumAgentOutput:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(
            generate_structured_with_retry(
                client,
                request,
                CurriculumAgentOutput,
                policy=retry_policy,
                observer=observer,
            ),
        )
    raise LLMProviderError(
        "LLM curriculum agent requires the sync service boundary to run "
        "outside an active event loop.",
        provider="adapter",
        retryable=False,
    )


def _build_schema_focused_prompt(payload: CurriculumAgentInput) -> str:
    weak = _concept_mastery_list(
        payload.knowledge_map.concepts, payload.knowledge_map.weak_concepts
    )
    missing = _concept_mastery_list(
        payload.knowledge_map.concepts, payload.knowledge_map.missing_concepts
    )
    developing = _concept_mastery_list(
        payload.knowledge_map.concepts,
        payload.knowledge_map.developing_concepts,
    )
    strong = _concept_mastery_list(
        payload.knowledge_map.concepts, payload.knowledge_map.strong_concepts
    )
    recommendations = _recommendation_lines(payload.critic_recommendations)

    return (
        "You are PathAI's curriculum transformation component. "
        "Return strict JSON only for CurriculumAgentOutput. "
        "Do not include markdown, commentary, secrets, provider metadata, or raw prompts.\n\n"
        f"Goal: {_bounded(payload.goal_text, 500)}\n\n"
        f"Duration: {payload.duration_weeks} weeks at {payload.hours_per_week} hours/week\n\n"
        f"Weak concepts: {weak}\n"
        f"Missing concepts: {missing}\n"
        f"Developing concepts: {developing}\n"
        f"Strong concepts: {strong}\n\n"
        f"Critic recommendations:\n{recommendations}\n\n"
        "Required JSON fields: title, duration_weeks, weeks, target_outcomes, assumptions. "
        "Each week must include week_number, theme, and topics (list of CurriculumTopicDTO). "
        "Each topic must include topic_id, title, concept_ids, difficulty, and estimated_hours. "
        "Use only difficulty values: beginner, intermediate, advanced."
    )


def _concept_mastery_list(
    all_concepts: list[ConceptMasteryDTO],
    concept_ids: list[str],
) -> str:
    if not concept_ids:
        return "none"
    concept_map = {c.concept_id: c for c in all_concepts}
    return ", ".join(
        _bounded(concept_map[cid].label, 60)
        for cid in concept_ids
        if cid in concept_map
    )


def _recommendation_lines(recommendations: list[str]) -> str:
    if not recommendations:
        return "- no critic recommendations provided"
    return "\n".join(f"- {_bounded(r, 200)}" for r in recommendations)


def _bounded(value: str, max_length: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[: max_length - 3]}..."

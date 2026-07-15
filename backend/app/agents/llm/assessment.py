from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from app.agents.contracts import AssessorAgent
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
from app.schemas.assessment import (
    AssessmentAgentInput,
    AssessmentAgentOutput,
    AssessmentAnswerDTO,
    AssessmentScoreOutput,
)


@dataclass(slots=True)
class LLMAssessmentAgent:
    client: LLMClient
    fallback_agent: AssessorAgent | None = None
    fallback_on_error: bool = True
    retry_policy: LLMRetryPolicy = field(default_factory=LLMRetryPolicy)
    timeout_policy: LLMTimeoutPolicy = field(default_factory=LLMTimeoutPolicy)
    max_output_tokens: int = 2048

    agent_name: str = "assessment_llm"
    observer: LLMReliabilityObserver = field(default_factory=NullObserver)

    def generate_question(self, payload: AssessmentAgentInput) -> AssessmentAgentOutput:
        request = StructuredOutputRequest(
            prompt=_build_question_prompt(payload),
            schema_name=AssessmentAgentOutput.__name__,
            request_id="assessment_llm_agent_question",
            metadata=LLMModelMetadata(provider="adapter", model="assessment-agent"),
            timeout=self.timeout_policy,
            max_output_tokens=self.max_output_tokens,
            temperature=0.0,
        )
        try:
            return _run_structured_sync_question(
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
                        schema_name=AssessmentAgentOutput.__name__,
                        attempt=self.retry_policy.max_attempts,
                        max_attempts=self.retry_policy.max_attempts,
                        error_code=exc.error_code,
                        reason_code="fallback_to_deterministic",
                    ),
                )
                return self.fallback_agent.generate_question(payload)
            raise AgentError(
                self.agent_name,
                "LLM-backed assessment question generation failed safely.",
            ) from exc

    def score_answer(self, answer: AssessmentAnswerDTO) -> AssessmentScoreOutput:
        request = StructuredOutputRequest(
            prompt=_build_scoring_prompt(answer),
            schema_name=AssessmentScoreOutput.__name__,
            request_id="assessment_llm_agent_scoring",
            metadata=LLMModelMetadata(provider="adapter", model="assessment-agent"),
            timeout=self.timeout_policy,
            max_output_tokens=self.max_output_tokens,
            temperature=0.0,
        )
        try:
            return _run_structured_sync_scoring(
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
                        schema_name=AssessmentScoreOutput.__name__,
                        attempt=self.retry_policy.max_attempts,
                        max_attempts=self.retry_policy.max_attempts,
                        error_code=exc.error_code,
                        reason_code="fallback_to_deterministic",
                    ),
                )
                return self.fallback_agent.score_answer(answer)
            raise AgentError(
                self.agent_name,
                "LLM-backed assessment answer scoring failed safely.",
            ) from exc


def _run_structured_sync_question(
    client: LLMClient,
    request: StructuredOutputRequest,
    retry_policy: LLMRetryPolicy,
    observer: LLMReliabilityObserver,
) -> AssessmentAgentOutput:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(
            generate_structured_with_retry(
                client,
                request,
                AssessmentAgentOutput,
                policy=retry_policy,
                observer=observer,
            ),
        )
    raise LLMProviderError(
        "LLM assessment agent requires the sync service boundary to run outside "
        "an active event loop.",
        provider="adapter",
        retryable=False,
    )


def _run_structured_sync_scoring(
    client: LLMClient,
    request: StructuredOutputRequest,
    retry_policy: LLMRetryPolicy,
    observer: LLMReliabilityObserver,
) -> AssessmentScoreOutput:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(
            generate_structured_with_retry(
                client,
                request,
                AssessmentScoreOutput,
                policy=retry_policy,
                observer=observer,
            ),
        )
    raise LLMProviderError(
        "LLM assessment agent requires the sync service boundary to run outside "
        "an active event loop.",
        provider="adapter",
        retryable=False,
    )


def _build_question_prompt(payload: AssessmentAgentInput) -> str:
    prior_summary = "\n".join(
        f"- Q{i+1}: {answer.question.prompt[:60]}... (score: {answer.score:.2f})"
        for i, answer in enumerate(payload.prior_answers[-3:])
    )
    if not prior_summary:
        prior_summary = "- no prior questions"

    concepts = ", ".join(payload.target_concepts[:6])

    return (
        "You are PathAI's assessment question-generation component. "
        "Return strict JSON only for AssessmentAgentOutput. "
        "Do not include markdown, commentary, secrets, provider metadata, or raw prompts.\n\n"
        f"Goal: {_bounded(payload.goal_text, 300)}\n\n"
        f"Learner strengths: {', '.join(payload.learner_profile.strengths[:4])}\n"
        f"Learner weak areas: {', '.join(payload.learner_profile.weak_areas[:4])}\n"
        f"Target concepts: {concepts}\n"
        f"Current confidence: {payload.current_confidence:.2f}\n"
        f"Questions asked: {payload.question_count}\n\n"
        "Recent questions:\n"
        f"{prior_summary}\n\n"
        "Required JSON fields: question (with question_id, question_type, prompt, options, "
        "target_concepts, difficulty), rationale, estimated_information_gain.\n"
        "Strict value rules (output is rejected otherwise):\n"
        "- question_id: must start with 'question_' followed by lowercase letters, digits "
        "or underscores, e.g. 'question_nlp_basics_1'.\n"
        "- question_type: exactly one of 'multiple_choice', 'short_answer', 'self_rating'.\n"
        "- difficulty: exactly one of 'beginner', 'intermediate', 'advanced' "
        "(never 'easy'/'hard').\n"
        "- target_concepts: 1-8 lowercase snake_case ids drawn from the provided target "
        "concepts, e.g. 'natural_language_processing'.\n"
        "- estimated_information_gain: a number between 0.0 and 1.0."
    )


def _build_scoring_prompt(answer: AssessmentAnswerDTO) -> str:
    concepts = ", ".join(answer.question.target_concepts[:6])

    answer_text = answer.answer_text or "no text answer"
    options = (
        ", ".join(answer.selected_options)
        if answer.selected_options
        else "no options selected"
    )

    return (
        "You are PathAI's assessment answer-scoring component. "
        "Return strict JSON only for AssessmentScoreOutput. "
        "Do not include markdown, commentary, secrets, provider metadata, or raw prompts.\n\n"
        f"Question: {answer.question.prompt}\n"
        f"Question type: {answer.question.question_type}\n"
        f"Question difficulty: {answer.question.difficulty}\n"
        f"Target concepts: {concepts}\n"
        f"Correct options: {', '.join(answer.question.options[:4])}\n\n"
        f"Learner answer text: {answer_text}\n"
        f"Learner selected options: {options}\n\n"
        "Required JSON fields: answer_id, score (0.0 to 1.0), concept_scores (non-empty list "
        "with concept_id, score_delta, evidence), feedback, confidence_after_answer.\n"
        "Strict value rules (output is rejected otherwise):\n"
        "- answer_id: must start with 'answer_' followed by lowercase letters, digits or "
        "underscores, e.g. 'answer_nlp_1'.\n"
        "- concept_scores[].concept_id: lowercase snake_case, drawn from the question's "
        "target_concepts.\n"
        "- concept_scores[].score_delta: a number between -1.0 and 1.0.\n"
        "- concept_scores[].evidence: 1-400 chars of actionable feedback.\n"
        "- score and confidence_after_answer: numbers between 0.0 and 1.0.\n"
        "Score must reflect answer quality."
    )


def _bounded(value: str, max_length: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[: max_length - 3]}..."

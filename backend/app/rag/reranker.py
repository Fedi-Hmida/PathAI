import json

from app.llm.mock import MockLLMClient
from app.llm.redaction import redact_for_llm
from app.llm.structured import generate_structured
from app.llm.types import LLMMessage
from app.prompts import get_prompt_registry
from app.rag.schemas import (
    ResourceCandidate,
    ResourceRerankedCandidate,
    ResourceRerankRequest,
    ResourceRerankResult,
)


class DeterministicResourceReranker:
    def rerank(self, request: ResourceRerankRequest) -> ResourceRerankResult:
        ranked: list[ResourceRerankedCandidate] = []
        seen_types: set[str] = set()
        remaining = request.candidates.copy()
        while remaining and len(ranked) < request.top_k:
            candidate = max(
                remaining,
                key=lambda item: (
                    _diversity_boost(item, seen_types),
                    item.match_score,
                    item.quality_score,
                    item.resource.foundational,
                ),
            )
            remaining.remove(candidate)
            seen_types.add(candidate.resource.type)
            ranked.append(
                ResourceRerankedCandidate(
                    resource_id=candidate.resource.resource_id,
                    rank=len(ranked) + 1,
                    score=round(candidate.match_score, 4),
                    why_this=candidate.why_this,
                )
            )
        return ResourceRerankResult(
            topic=request.topic,
            ranked_candidates=ranked,
            rationale=(
                "Deterministic reranking prioritized match score, resource quality, "
                "foundational status, accessibility, and lightweight type diversity."
            ),
            used_mock_llm=False,
        )


async def rerank_with_mock_llm(request: ResourceRerankRequest) -> ResourceRerankResult:
    deterministic = DeterministicResourceReranker().rerank(request)
    prompt = get_prompt_registry().render(
        "resource_rerank",
        {
            "learner_goal": request.goal or "No learner goal provided.",
            "topic": request.topic,
            "difficulty": request.difficulty,
            "knowledge_map_context": json.dumps(request.knowledge_map, sort_keys=True),
            "candidate_resources": json.dumps(
                [candidate.model_dump(mode="json") for candidate in request.candidates],
                sort_keys=True,
            ),
            "required_output_schema": ResourceRerankResult.model_json_schema(),
        },
    )
    payload = deterministic.model_copy(update={"used_mock_llm": True}).model_dump_json()
    return await generate_structured(
        client=MockLLMClient(responses=[payload]),
        messages=[LLMMessage(role="user", content=redact_for_llm(prompt.content))],
        output_model=ResourceRerankResult,
    )


def _diversity_boost(candidate: ResourceCandidate, seen_types: set[str]) -> float:
    return 0.04 if candidate.resource.type not in seen_types else 0.0

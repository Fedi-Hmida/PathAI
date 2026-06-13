import json

from app.critic.rubric import review_with_deterministic_rubric
from app.critic.schemas import CriticReviewRequest, CriticReviewResult
from app.llm.mock import MockLLMClient
from app.llm.redaction import redact_for_llm
from app.llm.structured import generate_structured
from app.llm.types import LLMMessage
from app.prompts import get_prompt_registry


async def review_with_mock_llm(request: CriticReviewRequest) -> CriticReviewResult:
    deterministic = review_with_deterministic_rubric(request)
    prompt = get_prompt_registry().render(
        "critic_review",
        {
            "learner_goal": request.curriculum.goal,
            "knowledge_map": json.dumps(
                request.curriculum.knowledge_map.model_dump(mode="json"),
                sort_keys=True,
            ),
            "curriculum_json": json.dumps(
                request.curriculum.model_dump(mode="json"),
                sort_keys=True,
            ),
            "resource_attachment_json": json.dumps(
                request.resource_attachment.model_dump(mode="json")
                if request.resource_attachment is not None
                else {},
                sort_keys=True,
            ),
            "rubric_criteria": (
                "Evaluate pacing, prerequisites, difficulty progression, resource coverage, "
                "resource diversity, URL validity, and why_this explanation specificity."
            ),
            "required_output_schema": json.dumps(
                CriticReviewResult.model_json_schema(),
                sort_keys=True,
            ),
        },
    )
    payload = deterministic.model_copy(update={"source": "mock_llm"}).model_dump_json()
    return await generate_structured(
        client=MockLLMClient(responses=[payload]),
        messages=[LLMMessage(role="user", content=redact_for_llm(prompt.content))],
        output_model=CriticReviewResult,
    )

from app.core.config import Settings, get_settings
from app.curriculum.schemas import CurriculumGenerationRequest, CurriculumPlan
from app.llm.client import LLMClientProtocol, UniversityLLMClient
from app.llm.config import assert_real_llm_configured
from app.llm.errors import LLMConfigurationError, LLMError
from app.llm.mock import MockLLMClient
from app.llm.redaction import redact_for_llm
from app.llm.structured import generate_structured
from app.llm.types import LLMMessage, LLMRequestOptions
from app.prompts import PromptRenderError, get_prompt_registry


async def generate_curriculum_with_llm(
    request: CurriculumGenerationRequest,
    deterministic_plan: CurriculumPlan,
    settings: Settings | None = None,
) -> CurriculumPlan:
    active_settings = settings or get_settings()
    if active_settings.llm_mock_mode:
        mock_plan = deterministic_plan.model_copy(update={"source": "mock_llm"})
        client: LLMClientProtocol = MockLLMClient(responses=[mock_plan.model_dump_json()])
    else:
        try:
            assert_real_llm_configured(active_settings)
        except LLMConfigurationError:
            return deterministic_plan
        client = UniversityLLMClient(settings=active_settings)

    try:
        prompt = get_prompt_registry(active_settings).render(
            "curriculum_generate_plan",
            {
                "goal": request.goal or deterministic_plan.goal,
                "timeline_weeks": request.timeline_weeks or deterministic_plan.timeline_weeks,
                "hours_per_week": request.hours_per_week or deterministic_plan.hours_per_week,
                "knowledge_map": deterministic_plan.knowledge_map.model_dump_json(),
                "draft_curriculum_json": deterministic_plan.model_dump_json(),
            },
        )
        generated = await generate_structured(
            client=client,
            messages=[LLMMessage(role="user", content=redact_for_llm(prompt.content))],
            output_model=CurriculumPlan,
            options=LLMRequestOptions(max_tokens=6000, response_format={"type": "json_object"}),
        )
    except (LLMError, PromptRenderError):
        return deterministic_plan

    return generated.model_copy(
        update={
            "curriculum_id": deterministic_plan.curriculum_id,
            "source": "mock_llm" if active_settings.llm_mock_mode else "real_llm",
        }
    )

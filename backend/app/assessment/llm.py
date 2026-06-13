import json

from app.assessment.constants import AssessmentQuestionSource
from app.assessment.schemas import AssessmentQuestion, GeneratedAssessmentQuestion
from app.core.config import Settings, get_settings
from app.llm.client import LLMClientProtocol, UniversityLLMClient
from app.llm.config import assert_real_llm_configured
from app.llm.errors import LLMConfigurationError, LLMError
from app.llm.mock import MockLLMClient
from app.llm.redaction import redact_for_llm
from app.llm.structured import generate_structured
from app.llm.types import LLMMessage, LLMRequestOptions
from app.prompts import PromptRenderError, get_prompt_registry


async def generate_assessment_question(
    goal: str,
    fallback_question: AssessmentQuestion,
    settings: Settings | None = None,
) -> AssessmentQuestion:
    active_settings = settings or get_settings()
    prompt = _render_question_prompt(
        goal=goal,
        fallback_question=fallback_question,
        settings=active_settings,
    )

    if active_settings.llm_mock_mode:
        mock_payload = _question_to_json(fallback_question)
        client: LLMClientProtocol = MockLLMClient(responses=[mock_payload])
        source: AssessmentQuestionSource = "mock_llm"
    else:
        try:
            assert_real_llm_configured(active_settings)
        except LLMConfigurationError:
            return fallback_question
        client = UniversityLLMClient(settings=active_settings)
        source = "real_llm"

    try:
        draft = await generate_structured(
            client=client,
            messages=[LLMMessage(role="user", content=redact_for_llm(prompt))],
            output_model=GeneratedAssessmentQuestion,
            options=LLMRequestOptions(max_tokens=700, response_format={"type": "json_object"}),
        )
    except (LLMError, PromptRenderError):
        return fallback_question

    return AssessmentQuestion(
        question_id=fallback_question.question_id,
        topic=draft.topic,
        prompt=draft.question,
        question_type=draft.question_type,
        difficulty=draft.difficulty,
        options=draft.options,
        expected_concepts=draft.expected_concepts,
        skill_tags=draft.skill_tags,
        source=source,
    )


def _render_question_prompt(
    goal: str,
    fallback_question: AssessmentQuestion,
    settings: Settings,
) -> str:
    rendered = get_prompt_registry(settings).render(
        "assessment_generate_question",
        {
            "goal": goal,
            "topic": fallback_question.topic,
            "difficulty": fallback_question.difficulty,
            "expected_concepts": ", ".join(fallback_question.expected_concepts),
        },
    )
    return rendered.content


def _question_to_json(question: AssessmentQuestion) -> str:
    payload = {
        "question": question.prompt,
        "topic": question.topic,
        "question_type": question.question_type,
        "difficulty": question.difficulty,
        "options": question.options,
        "expected_concepts": question.expected_concepts,
        "skill_tags": question.skill_tags,
    }
    return json.dumps(payload)

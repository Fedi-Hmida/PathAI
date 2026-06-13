import json

from app.llm.mock import MockLLMClient
from app.llm.redaction import redact_for_llm
from app.llm.structured import generate_structured
from app.llm.types import LLMMessage
from app.prompts import get_prompt_registry
from app.quiz.generator import generate_deterministic_quiz
from app.quiz.schemas import Quiz, QuizGenerationRequest


async def generate_quiz_with_optional_mock_llm(
    request: QuizGenerationRequest,
    deterministic_quiz: Quiz | None = None,
) -> Quiz:
    fallback = deterministic_quiz or generate_deterministic_quiz(request)
    if not request.use_mock_llm:
        return fallback

    prompt = get_prompt_registry().render(
        "quiz_generate",
        {
            "learner_goal": request.curriculum.goal,
            "week_theme": _week_theme(request),
            "topics": ", ".join(fallback.topic_names),
            "difficulty": fallback.questions[0].difficulty,
            "resources": _resource_context(request),
            "required_output_schema": "Return JSON matching the Quiz schema.",
        },
    )
    messages = [LLMMessage(role="user", content=redact_for_llm(prompt.content))]
    return await generate_structured(
        client=MockLLMClient(
            responses=[json.dumps(fallback.model_dump(mode="json"))],
        ),
        messages=messages,
        output_model=Quiz,
    )


def _week_theme(request: QuizGenerationRequest) -> str:
    for week in request.curriculum.weeks:
        if week.week_number == request.week_number:
            return week.theme
    return "unknown week"


def _resource_context(request: QuizGenerationRequest) -> str:
    if request.resource_attachment is None:
        return "No resource attachment was provided."
    titles = [
        resource.title
        for attachment in request.resource_attachment.attachments
        for resource in attachment.resources
    ]
    return ", ".join(titles[:8]) if titles else "No attached resources."

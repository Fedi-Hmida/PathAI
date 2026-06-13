import json
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.llm.client import LLMClientProtocol
from app.llm.errors import InvalidJSONError, SchemaValidationError
from app.llm.types import LLMMessage, LLMRequestOptions

TModel = TypeVar("TModel", bound=BaseModel)


async def generate_structured(
    client: LLMClientProtocol,
    messages: list[LLMMessage],
    output_model: type[TModel],
    options: LLMRequestOptions | None = None,
) -> TModel:
    request_options = options or LLMRequestOptions(response_format={"type": "json_object"})
    response = await client.complete(messages=messages, options=request_options)
    return parse_structured_output(response.content, output_model)


def parse_structured_output(content: str, output_model: type[TModel]) -> TModel:
    json_text = extract_json_text(content)
    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise InvalidJSONError("LLM output was not valid JSON.") from exc

    try:
        return output_model.model_validate(payload)
    except ValidationError as exc:
        raise SchemaValidationError("LLM output did not match the expected schema.") from exc


def extract_json_text(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise InvalidJSONError("LLM output did not contain a JSON object.")
    return stripped[start : end + 1]

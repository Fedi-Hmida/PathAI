from __future__ import annotations

import json
from json import JSONDecodeError
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.llm.errors import LLMOutputParseError, LLMOutputValidationError

StructuredModel = TypeVar("StructuredModel", bound=BaseModel)


def parse_structured_output(
    raw_text: str,
    output_schema: type[StructuredModel],
) -> StructuredModel:
    json_text = extract_json_text(raw_text)
    try:
        payload = json.loads(json_text)
    except JSONDecodeError as exc:
        raise LLMOutputParseError("LLM output did not contain valid JSON.") from exc
    try:
        return output_schema.model_validate(payload)
    except ValidationError as exc:
        raise LLMOutputValidationError(
            f"LLM output failed schema validation for {output_schema.__name__}.",
        ) from exc


def extract_json_text(raw_text: str) -> str:
    text = raw_text.strip()
    if not text:
        raise LLMOutputParseError("LLM output was empty.")

    fenced = _extract_fenced_json(text)
    if fenced is not None:
        return fenced

    balanced = _extract_balanced_json(text)
    if balanced is None:
        raise LLMOutputParseError("LLM output did not include a JSON object or array.")
    return balanced


def _extract_fenced_json(text: str) -> str | None:
    fence = "```"
    start = text.find(fence)
    if start < 0:
        return None
    content_start = start + len(fence)
    content_end = text.find(fence, content_start)
    if content_end < 0:
        return None
    content = text[content_start:content_end].strip()
    if content.lower().startswith("json"):
        content = content[4:].strip()
    return content or None


def _extract_balanced_json(text: str) -> str | None:
    start = _first_json_start(text)
    if start is None:
        return None

    stack: list[str] = []
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = in_string
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char in "{[":
            stack.append("}" if char == "{" else "]")
        elif char in "}]":
            if not stack or stack[-1] != char:
                raise LLMOutputParseError("LLM output contained malformed JSON.")
            stack.pop()
            if not stack:
                return text[start : index + 1]
    raise LLMOutputParseError("LLM output contained incomplete JSON.")


def _first_json_start(text: str) -> int | None:
    candidates = [index for index in (text.find("{"), text.find("[")) if index >= 0]
    if not candidates:
        return None
    return min(candidates)

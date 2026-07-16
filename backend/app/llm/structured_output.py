from __future__ import annotations

import json
from json import JSONDecodeError
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.llm.contracts import StructuredOutputRequest
from app.llm.errors import (
    LLMOutputParseError,
    LLMOutputValidationError,
    LLMStructuredOutputError,
)
from app.llm.redaction import redact_secrets

StructuredModel = TypeVar("StructuredModel", bound=BaseModel)

# Cap on the field-level repair hint so a schema with many errors cannot
# balloon the repair prompt. Bounded and secret-free by construction.
_MAX_REPAIR_HINT_CHARS = 800
# The request prompt is bounded at 12000 chars (StructuredOutputRequest); keep
# the repaired prompt within that so model_copy never fails validation.
_MAX_PROMPT_CHARS = 12000


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
            repair_hint=_build_validation_repair_hint(exc),
        ) from exc


def _build_validation_repair_hint(error: ValidationError) -> str:
    """Summarize a pydantic ValidationError as bounded, secret-free field guidance.

    Keeps only `loc`/`type`/`msg` and explicitly drops `input` and `ctx` (which
    can echo the offending model output or user content) via pydantic's own
    `include_input=False` / `include_context=False`. The result is redacted and
    length-capped, so it is safe to append to a prompt or store on an error.
    """
    parts: list[str] = []
    for item in error.errors(include_url=False, include_context=False, include_input=False):
        loc = ".".join(str(segment) for segment in item.get("loc", ())) or "<root>"
        message = str(item.get("msg", "")).strip()
        error_type = str(item.get("type", "")).strip()
        parts.append(f"{loc}: {message} ({error_type})")
    hint = redact_secrets("; ".join(parts))
    return hint[:_MAX_REPAIR_HINT_CHARS]


def build_repair_request(
    request: StructuredOutputRequest,
    error: LLMStructuredOutputError,
    *,
    temperature: float,
) -> StructuredOutputRequest:
    """Build the next attempt's request for an in-band self-correction retry.

    Appends a secret-free "your previous reply was invalid, return corrected
    strict JSON" instruction (with the field-level repair hint when available)
    to the original prompt, and nudges the temperature up only — never down —
    so a deterministic bad local output can be escaped. This is a genuinely
    different request, so the model can actually fix the output.
    """
    if error.repair_hint:
        detail = f"The following fields were invalid: {error.repair_hint}"
    else:
        detail = "Your previous response could not be parsed as the required JSON."

    instruction = (
        "Your previous response was invalid and could not be used. "
        f"{detail} "
        "Return a corrected response as a single strict JSON object that matches "
        "the required schema exactly, with no commentary or markdown."
    )
    new_prompt = f"{request.prompt}\n\n{instruction}"[:_MAX_PROMPT_CHARS]
    return request.model_copy(
        update={
            "prompt": new_prompt,
            "temperature": max(request.temperature, temperature),
        },
    )


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

import json
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlparse

from app.rag.schemas import ResourceDocumentPayload, ResourceSeed

JsonObject = dict[str, Any]


class ResourceSeedValidationError(ValueError):
    """Raised when a curated resource seed payload violates the seed schema."""


def load_json_object(path: Path) -> JsonObject:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ResourceSeedValidationError(f"{path} must contain one JSON object.")
    return cast(JsonObject, payload)


def load_resource_seed(path: Path, schema: Mapping[str, Any]) -> ResourceSeed:
    payload = load_json_object(path)
    validate_resource_seed_against_json_schema(payload, schema)
    return ResourceSeed.model_validate(payload)


def load_resource_seeds_from_directory(
    directory: Path,
    schema: Mapping[str, Any],
) -> list[ResourceSeed]:
    if not directory.exists():
        raise ResourceSeedValidationError(f"Resource directory does not exist: {directory}.")
    if not directory.is_dir():
        raise ResourceSeedValidationError(f"Resource path is not a directory: {directory}.")

    seeds: list[ResourceSeed] = []
    for path in sorted(directory.glob("*.json")):
        seeds.append(load_resource_seed(path, schema))
    return seeds


def load_resource_seeds_from_directories(
    directories: list[Path],
    schema: Mapping[str, Any],
) -> list[ResourceSeed]:
    seeds: list[ResourceSeed] = []
    for directory in directories:
        seeds.extend(load_resource_seeds_from_directory(directory, schema))
    return seeds


def map_seed_to_document_payload(seed: ResourceSeed) -> ResourceDocumentPayload:
    return seed.to_resource_document_payload()


def validate_resource_seed_against_json_schema(
    payload: Mapping[str, Any],
    schema: Mapping[str, Any],
) -> None:
    if schema.get("type") != "object":
        raise ResourceSeedValidationError("Resource seed schema must describe an object.")

    required = _string_list(schema.get("required"))
    missing = [field for field in required if field not in payload]
    if missing:
        raise ResourceSeedValidationError(f"Resource seed is missing fields: {', '.join(missing)}.")

    properties = _properties(schema)
    if schema.get("additionalProperties") is False:
        extra = [field for field in payload if field not in properties]
        if extra:
            raise ResourceSeedValidationError(
                f"Resource seed contains unsupported fields: {', '.join(extra)}."
            )

    for field, value in payload.items():
        rules = properties.get(field)
        if rules is not None:
            _validate_field(field, value, rules)


def _properties(schema: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    raw_properties = schema.get("properties")
    if not isinstance(raw_properties, dict):
        raise ResourceSeedValidationError("Resource seed schema is missing properties.")
    properties: dict[str, Mapping[str, Any]] = {}
    for key, value in raw_properties.items():
        if isinstance(key, str) and isinstance(value, Mapping):
            properties[key] = value
    return properties


def _validate_field(field: str, value: Any, rules: Mapping[str, Any]) -> None:
    schema_type = rules.get("type")
    if schema_type == "string":
        _validate_string(field, value, rules)
    elif schema_type == "array":
        _validate_array(field, value, rules)
    elif schema_type == "integer":
        _validate_integer(field, value, rules)
    elif schema_type == "number":
        _validate_number(field, value, rules)
    elif schema_type == "boolean" and not isinstance(value, bool):
        raise ResourceSeedValidationError(f"{field} must be a boolean.")

    enum_values = rules.get("enum")
    if isinstance(enum_values, list) and value not in enum_values:
        raise ResourceSeedValidationError(f"{field} must be one of: {', '.join(enum_values)}.")


def _validate_string(field: str, value: Any, rules: Mapping[str, Any]) -> None:
    if not isinstance(value, str):
        raise ResourceSeedValidationError(f"{field} must be a string.")
    min_length = rules.get("minLength")
    if isinstance(min_length, int) and len(value) < min_length:
        raise ResourceSeedValidationError(f"{field} is shorter than {min_length} characters.")
    text_format = rules.get("format")
    if text_format == "uri" and not _is_http_url(value):
        raise ResourceSeedValidationError(f"{field} must be an absolute HTTP(S) URL.")
    if text_format == "date":
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise ResourceSeedValidationError(f"{field} must be an ISO date.") from exc


def _validate_array(field: str, value: Any, rules: Mapping[str, Any]) -> None:
    if not isinstance(value, list):
        raise ResourceSeedValidationError(f"{field} must be an array.")
    min_items = rules.get("minItems")
    if isinstance(min_items, int) and len(value) < min_items:
        raise ResourceSeedValidationError(f"{field} must contain at least {min_items} item(s).")
    items = rules.get("items")
    if isinstance(items, Mapping) and items.get("type") == "string":
        if not all(isinstance(item, str) and item.strip() for item in value):
            raise ResourceSeedValidationError(f"{field} must contain non-empty strings.")


def _validate_integer(field: str, value: Any, rules: Mapping[str, Any]) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ResourceSeedValidationError(f"{field} must be an integer.")
    minimum = rules.get("minimum")
    if isinstance(minimum, int | float) and value < minimum:
        raise ResourceSeedValidationError(f"{field} must be at least {minimum}.")


def _validate_number(field: str, value: Any, rules: Mapping[str, Any]) -> None:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ResourceSeedValidationError(f"{field} must be a number.")
    minimum = rules.get("minimum")
    maximum = rules.get("maximum")
    if isinstance(minimum, int | float) and value < minimum:
        raise ResourceSeedValidationError(f"{field} must be at least {minimum}.")
    if isinstance(maximum, int | float) and value > maximum:
        raise ResourceSeedValidationError(f"{field} must be at most {maximum}.")


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ResourceSeedValidationError("Resource seed schema has an invalid required list.")
    return value

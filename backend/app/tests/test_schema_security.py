from __future__ import annotations

import inspect
import re
from collections.abc import Iterator

from pydantic import BaseModel

from app.fixtures import canonical_demo, mock_agents

SECRET_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"api[_-]?key",
        r"\bsecret\b",
        r"\bpassword\b",
        r"\btoken\b",
        r"bearer\s+",
        r"mongodb(\+srv)?://",
        r"sk-[A-Za-z0-9]",
        r"-----BEGIN",
    ]
]


def iter_strings(value: object) -> Iterator[str]:
    if isinstance(value, BaseModel):
        yield from iter_strings(value.model_dump(mode="json"))
    elif isinstance(value, dict):
        for key, nested_value in value.items():
            yield str(key)
            yield from iter_strings(nested_value)
    elif isinstance(value, list | tuple | set):
        for nested_value in value:
            yield from iter_strings(nested_value)
    elif isinstance(value, str):
        yield value


def public_fixture_values() -> Iterator[object]:
    for module in [canonical_demo, mock_agents]:
        for name in dir(module):
            if name.isupper():
                yield getattr(module, name)


def test_fixture_values_do_not_contain_secret_like_strings() -> None:
    for value in public_fixture_values():
        for text in iter_strings(value):
            for pattern in SECRET_PATTERNS:
                assert pattern.search(text) is None


def test_fixture_modules_do_not_reference_env_or_external_clients() -> None:
    for module in [canonical_demo, mock_agents]:
        source = inspect.getsource(module)
        assert ".env" not in source
        assert "os.getenv" not in source
        assert "httpx" not in source
        assert "pymongo" not in source
        assert "motor" not in source

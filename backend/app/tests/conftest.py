import os
from collections.abc import Iterator

import pytest

from app.core.config import get_settings

os.environ["LLM_MOCK_MODE"] = "true"


@pytest.fixture(autouse=True)
def force_mock_llm_mode(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("LLM_MOCK_MODE", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()

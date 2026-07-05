import os
from pathlib import Path

import pytest

from app.core.settings import Settings
from app.llm.structured_output_spike import (
    LiveLLMNotConfiguredError,
    load_live_settings_from_env_file,
    run_optional_live_structured_output_spike,
)
from app.schemas.llm_spike import MiniKnowledgeMapOutput

pytestmark = pytest.mark.skipif(
    os.getenv("ENABLE_LIVE_LLM_TESTS", "false").lower() != "true",
    reason="Live LLM spike tests are optional and disabled by default.",
)


@pytest.mark.asyncio
@pytest.mark.live_llm
async def test_live_llm_spike_is_skipped_unless_enabled() -> None:
    settings = Settings(enable_live_llm_tests=False)

    with pytest.raises(LiveLLMNotConfiguredError):
        await run_optional_live_structured_output_spike(settings, MiniKnowledgeMapOutput)


@pytest.mark.asyncio
@pytest.mark.live_llm
async def test_live_llm_spike_requires_non_mock_provider() -> None:
    settings = Settings(enable_live_llm_tests=True, llm_provider="mock")

    with pytest.raises(LiveLLMNotConfiguredError):
        await run_optional_live_structured_output_spike(settings, MiniKnowledgeMapOutput)


@pytest.mark.asyncio
@pytest.mark.live_llm
async def test_live_llm_spike_from_env_file() -> None:
    settings = load_live_settings_from_env_file(Path(__file__).parents[3] / ".env")

    result = await run_optional_live_structured_output_spike(settings, MiniKnowledgeMapOutput)

    assert result.concepts

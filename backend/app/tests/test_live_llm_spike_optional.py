import os

import pytest

from app.core.settings import Settings
from app.llm.live_client import (
    LIVE_LLM_OPT_IN_ENV_VAR,
    LiveLLMSmokeResponse,
    build_live_client_from_settings,
    run_live_structured_output_smoke,
)

pytestmark = pytest.mark.skipif(
    os.getenv(LIVE_LLM_OPT_IN_ENV_VAR, "").lower() not in {"1", "true", "yes"},
    reason=(
        "Live LLM smoke tests are optional and require "
        f"{LIVE_LLM_OPT_IN_ENV_VAR}=1."
    ),
)


def _live_settings_or_skip() -> Settings:
    settings = Settings()
    try:
        build_live_client_from_settings(settings)
    except RuntimeError as exc:
        pytest.skip(str(exc))
    return settings


@pytest.mark.asyncio
@pytest.mark.live_llm
async def test_live_llm_smoke_returns_minimal_structured_json() -> None:
    settings = _live_settings_or_skip()

    result = await run_live_structured_output_smoke(settings, LiveLLMSmokeResponse)

    assert result.status == "ok"
    assert result.message

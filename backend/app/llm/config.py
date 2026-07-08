from __future__ import annotations

from pydantic import BaseModel, Field

LLM_ENV_VAR_NAMES: tuple[str, ...] = (
    "LLM_PROVIDER",
    "LLM_MODEL",
    "LLM_BASE_URL",
    "LLM_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_API_KEY",
    "UNIVERSITY_LLM_API_URL",
    "UNIVERSITY_LLM_API_KEY",
    "UNIVERSITY_LLM_MODEL",
    "LLM_TIMEOUT_SECONDS",
    "ENABLE_LIVE_LLM_TESTS",
    "PATHAI_ENABLE_LLM_ASSESSMENT_AGENT",
    "PATHAI_ENABLE_LLM_KNOWLEDGE_MAP_AGENT",
    "PATHAI_ENABLE_LLM_CRITIC_AGENT",
    "PATHAI_ENABLE_LLM_CURRICULUM_AGENT",
)


class LLMAdapterConfig(BaseModel):
    provider: str = Field(default="fake", min_length=1, max_length=80)
    model: str = Field(default="deterministic-fake", min_length=1, max_length=120)
    timeout_seconds: int = Field(default=45, ge=1, le=300)
    max_output_tokens: int = Field(default=2048, ge=1, le=32000)
    max_attempts: int = Field(default=2, ge=1, le=5)
    live_enabled: bool = False
    knowledge_map_agent_enabled: bool = False
    fallback_to_deterministic: bool = True
    env_var_names: tuple[str, ...] = LLM_ENV_VAR_NAMES

    @classmethod
    def default_fake(cls) -> LLMAdapterConfig:
        return cls()

    def safe_summary(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "model": self.model,
            "timeout_seconds": self.timeout_seconds,
            "max_output_tokens": self.max_output_tokens,
            "max_attempts": self.max_attempts,
            "live_enabled": self.live_enabled,
            "knowledge_map_agent_enabled": self.knowledge_map_agent_enabled,
            "fallback_to_deterministic": self.fallback_to_deterministic,
            "env_var_names": list(self.env_var_names),
        }

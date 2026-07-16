from functools import lru_cache
from typing import Any

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables without reading .env files."""

    model_config = SettingsConfigDict(
        env_file=None,
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    app_name: str = "PathAI"
    app_env: str = "local"
    app_debug: bool = False
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    llm_provider: str = "mock"
    llm_base_url: str = ""
    llm_model: str = ""
    llm_api_key: SecretStr | None = None
    openai_base_url: str = ""
    openai_api_key: SecretStr | None = None
    university_llm_api_url: str = ""
    university_llm_api_key: SecretStr | None = None
    university_llm_model: str = ""
    llm_max_retries: int = Field(default=1, ge=0, le=5)
    llm_retry_backoff_seconds: float = Field(default=1.0, ge=0.0, le=30.0)
    llm_mock_mode: bool = True
    llm_timeout_seconds: int = Field(default=45, ge=1, le=300)
    enable_live_llm_tests: bool = False
    enable_llm_assessment_agent: bool = Field(
        default=False,
        validation_alias="PATHAI_ENABLE_LLM_ASSESSMENT_AGENT",
    )
    enable_llm_knowledge_map_agent: bool = Field(
        default=False,
        validation_alias="PATHAI_ENABLE_LLM_KNOWLEDGE_MAP_AGENT",
    )
    enable_llm_critic_agent: bool = Field(
        default=False,
        validation_alias="PATHAI_ENABLE_LLM_CRITIC_AGENT",
    )
    enable_llm_curriculum_agent: bool = Field(
        default=False,
        validation_alias="PATHAI_ENABLE_LLM_CURRICULUM_AGENT",
    )
    llm_fallback_mode: str = Field(
        default="fail_loud",
        validation_alias="PATHAI_LLM_FALLBACK_MODE",
    )
    llm_self_correction_enabled: bool = Field(
        default=True,
        validation_alias="PATHAI_LLM_SELF_CORRECTION",
    )
    mongodb_uri: str = ""
    mongodb_database_name: str = "pathai"
    repository_backend: str = "fake"
    enable_orchestration_run_route: bool = Field(
        default=True,
        validation_alias="PATHAI_ENABLE_ORCHESTRATION_RUN_ROUTE",
    )
    enable_auth: bool = Field(
        default=False,
        validation_alias="PATHAI_ENABLE_AUTH",
    )
    jwt_secret_key: SecretStr | None = None
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = Field(default=900, ge=60, le=3600)
    refresh_token_ttl_seconds: int = Field(default=1_209_600, ge=300, le=7_776_000)
    refresh_cookie_name: str = "pathai_refresh"
    refresh_cookie_secure: bool = True
    refresh_cookie_samesite: str = "lax"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @property
    def live_llm_configured(self) -> bool:
        if self.llm_provider.lower() == "mock":
            return self.llm_mock_mode
        return bool(
            self.effective_llm_base_url
            and self.effective_llm_model
            and self.effective_llm_api_key
        )

    @property
    def effective_llm_base_url(self) -> str:
        return self.llm_base_url or self.openai_base_url or self.university_llm_api_url

    @property
    def effective_llm_model(self) -> str:
        return self.llm_model or self.university_llm_model

    @property
    def effective_llm_api_key(self) -> SecretStr | None:
        return self.llm_api_key or self.openai_api_key or self.university_llm_api_key

    @property
    def llm_deterministic_fallback_enabled(self) -> bool:
        """True only when LLM-agent failures may silently degrade to deterministic output.

        Defaults to False (fail-loud): an enabled LLM agent that fails raises an
        explicit `LLMGenerationUnavailableError` instead of serving another
        topic's canned deterministic content. Set `PATHAI_LLM_FALLBACK_MODE`
        to `deterministic` only for offline tests / an intentional offline demo.
        """
        return self.llm_fallback_mode.strip().lower() == "deterministic"

    @property
    def auth_configured(self) -> bool:
        """True when auth is enabled and a signing secret is present.

        Never exposes the secret value itself; only whether one is set.
        """
        return self.enable_auth and self.jwt_secret_key is not None

    def readiness_flags(self) -> dict[str, Any]:
        return {
            "settings_loaded": True,
            "llm_provider": self.llm_provider,
            "llm_configured": self.live_llm_configured,
            "live_llm_enabled": self.enable_live_llm_tests,
            "llm_mock_mode": self.llm_mock_mode,
            "auth_enabled": self.enable_auth,
            "auth_configured": self.auth_configured,
        }

    def redacted_dict(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        for key in list(data):
            if self._is_sensitive_key(key):
                data[key] = "***REDACTED***" if data[key] else ""
        return data

    def __repr__(self) -> str:
        return f"Settings({self.redacted_dict()!r})"

    @staticmethod
    def _is_sensitive_key(key: str) -> bool:
        lowered = key.lower()
        return any(token in lowered for token in ("secret", "token", "key", "password", "uri"))


@lru_cache
def get_settings() -> Settings:
    return Settings()

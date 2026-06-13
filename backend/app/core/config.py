from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PathAI API"
    app_version: str = "0.1.0"
    app_env: Literal["local", "development", "test", "staging", "production"] = "local"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    enable_docs: bool = True

    enable_dev_endpoints: bool | None = None
    enable_demo_endpoints: bool | None = None
    demo_mode: bool = True
    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )
    rate_limit_enabled: bool = False
    rate_limit_requests_per_minute: int = Field(default=120, ge=1, le=10000)
    audit_log_enabled: bool = False
    redact_log_values: bool = True
    expose_internal_errors: bool | None = None
    trace_privacy_mode: Literal["strict", "metadata_only", "disabled"] = "strict"

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "pathai_dev"
    mongodb_server_selection_timeout_ms: int = 1000
    mongodb_connect_on_startup: bool = True

    jwt_secret_key: str = Field(default="change-me-in-real-env")
    jwt_algorithm: str = "HS256"
    jwt_expiry_days: int = 7

    university_llm_api_url: str = ""
    university_llm_api_key: str = ""
    openai_base_url: str = ""
    openai_api_key: str = ""
    university_llm_model: str = "pathai-university-default"
    llm_timeout_seconds: float = 30.0
    llm_max_retries: int = 2
    llm_retry_backoff_seconds: float = 0.5
    llm_mock_mode: bool = True
    llm_prompt_version: str = "v1"

    tavily_api_key: str = ""
    chroma_persist_dir: str = "./chroma_db"
    langsmith_api_key: str = ""
    langsmith_project: str = "pathai-dev"
    sentry_dsn: str = ""
    sendgrid_api_key: str = ""

    @property
    def llm_api_url(self) -> str:
        if self.university_llm_api_url:
            return self.university_llm_api_url
        if self.openai_base_url:
            return f"{self.openai_base_url.rstrip('/')}/chat/completions"
        return ""

    @property
    def llm_api_key(self) -> str:
        return self.university_llm_api_key or self.openai_api_key

    @property
    def dev_endpoints_enabled(self) -> bool:
        if self.enable_dev_endpoints is not None:
            return self.enable_dev_endpoints
        return self.app_env in {"local", "development", "test"}

    @property
    def demo_endpoints_enabled(self) -> bool:
        if self.enable_demo_endpoints is not None:
            return self.enable_demo_endpoints
        return self.app_env in {"local", "development", "test"} and self.demo_mode

    @property
    def internal_errors_exposed(self) -> bool:
        if self.expose_internal_errors is not None:
            return self.expose_internal_errors
        return self.app_env in {"local", "development", "test"}

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: Any) -> list[str] | Any:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

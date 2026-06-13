from app.core.config import Settings


def effective_allowed_origins(settings: Settings) -> list[str]:
    if settings.app_env == "production" and "*" in settings.allowed_origins:
        return ["*"]
    return settings.allowed_origins


def should_expose_internal_errors(settings: Settings) -> bool:
    return settings.internal_errors_exposed


def dev_endpoints_enabled(settings: Settings) -> bool:
    return settings.dev_endpoints_enabled


def demo_endpoints_enabled(settings: Settings) -> bool:
    return settings.demo_endpoints_enabled

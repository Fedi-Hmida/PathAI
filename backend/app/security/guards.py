from app.core.config import Settings
from app.security.constants import DEV_PATH_PREFIX, PUBLIC_API_PATHS
from app.security.settings import demo_endpoints_enabled, dev_endpoints_enabled


def is_dev_path(path: str, api_prefix: str) -> bool:
    return _strip_api_prefix(path, api_prefix).startswith(DEV_PATH_PREFIX)


def is_public_foundation_path(path: str, api_prefix: str) -> bool:
    return _strip_api_prefix(path, api_prefix) in PUBLIC_API_PATHS


def should_block_dev_path(path: str, settings: Settings) -> bool:
    return is_dev_path(path, settings.api_v1_prefix) and not dev_endpoints_enabled(settings)


def should_block_demo_path(path: str, settings: Settings) -> bool:
    if not path.startswith(settings.api_v1_prefix):
        return False
    if is_dev_path(path, settings.api_v1_prefix):
        return False
    if is_public_foundation_path(path, settings.api_v1_prefix):
        return False
    return not demo_endpoints_enabled(settings)


def _strip_api_prefix(path: str, api_prefix: str) -> str:
    if path == api_prefix:
        return "/"
    if path.startswith(f"{api_prefix}/"):
        return path.removeprefix(api_prefix)
    return path

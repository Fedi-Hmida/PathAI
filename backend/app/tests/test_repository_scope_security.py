from __future__ import annotations

import ast
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = [
    APP_ROOT / "repositories",
    APP_ROOT / "services",
]
FORBIDDEN_IMPORT_PREFIXES = (
    "app.agents",
    "app.api",
    "app.llm",
    "app.orchestration",
    "fastapi",
    "httpx",
    "langgraph",
    "requests",
    "urllib",
)
MONGO_DRIVER_PREFIXES = (
    "beanie",
    "motor",
    "pymongo",
)
MONGO_REPOSITORY_DIR = APP_ROOT / "repositories" / "mongo"


def test_repository_and_service_layers_do_not_import_forbidden_runtime_boundaries() -> None:
    violations: list[str] = []

    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    _collect_forbidden_import(path, alias.name, violations)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                _collect_forbidden_import(path, node.module, violations)

    assert violations == []


def test_only_mongo_repository_files_import_a_mongo_driver() -> None:
    violations: list[str] = []

    for path in _python_files():
        if _is_mongo_repository_file(path):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    _collect_forbidden_module(path, alias.name, MONGO_DRIVER_PREFIXES, violations)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                _collect_forbidden_module(path, node.module, MONGO_DRIVER_PREFIXES, violations)

    assert violations == []


def test_repository_and_service_layers_do_not_reference_env_files() -> None:
    offenders = [
        str(path.relative_to(APP_ROOT))
        for path in _python_files()
        if ".env" in path.read_text(encoding="utf-8")
    ]

    assert offenders == []


def _python_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        files.extend(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)
    return files


def _collect_forbidden_import(path: Path, module: str, violations: list[str]) -> None:
    _collect_forbidden_module(path, module, FORBIDDEN_IMPORT_PREFIXES, violations)


def _collect_forbidden_module(
    path: Path,
    module: str,
    prefixes: tuple[str, ...],
    violations: list[str],
) -> None:
    if module.startswith(prefixes):
        relative_path = path.relative_to(APP_ROOT)
        violations.append(f"{relative_path}: {module}")


def _is_mongo_repository_file(path: Path) -> bool:
    return MONGO_REPOSITORY_DIR in path.parents

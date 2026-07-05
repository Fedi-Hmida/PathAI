from __future__ import annotations

import importlib
import inspect
from types import ModuleType

SCHEMA_MODULES = [
    "app.schemas.base",
    "app.schemas.ids",
    "app.schemas.enums",
    "app.schemas.goal",
    "app.schemas.assessment",
    "app.schemas.knowledge_map",
    "app.schemas.curriculum",
    "app.schemas.resource",
    "app.schemas.progress",
    "app.schemas.quiz",
    "app.schemas.adaptation",
    "app.schemas.critic",
    "app.schemas.evaluation",
    "app.schemas.orchestration",
    "app.schemas.dashboard",
    "app.schemas.llm_spike",
]

FIXTURE_MODULES = [
    "app.fixtures.canonical_demo",
    "app.fixtures.mock_agents",
]

FORBIDDEN_IMPORT_SNIPPETS = [
    "app.services",
    "app.repositories",
    "app.db",
    "app.api",
    "langgraph",
    "pymongo",
    "motor",
]


def test_rebuild_2_schema_modules_import_cleanly() -> None:
    for module_name in SCHEMA_MODULES:
        module = importlib.import_module(module_name)
        assert isinstance(module, ModuleType)


def test_rebuild_2_fixture_modules_import_cleanly() -> None:
    for module_name in FIXTURE_MODULES:
        module = importlib.import_module(module_name)
        assert isinstance(module, ModuleType)


def test_schema_modules_do_not_import_future_phase_boundaries() -> None:
    for module_name in SCHEMA_MODULES:
        module = importlib.import_module(module_name)
        source = inspect.getsource(module)

        for forbidden in FORBIDDEN_IMPORT_SNIPPETS:
            assert forbidden not in source

from __future__ import annotations

import ast
import inspect
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.core.settings import Settings
from app.repositories.factory import build_repository_set
from app.schemas.enums import DifficultyLevel, GoalStatus
from app.schemas.goal import LearnerProfile, LearningGoalDTO
from scripts import reset_platform_data as reset_script


def _sample_goal() -> LearningGoalDTO:
    now = datetime.now(tz=UTC)
    return LearningGoalDTO(
        goal_id="goal_reset_script_test",
        run_id="run_reset_script_test",
        goal_text="Learn distributed systems fundamentals",
        normalized_goal_text="Learn distributed systems fundamentals",
        status=GoalStatus.CREATED,
        learner_profile=LearnerProfile(
            learner_type="reset script test learner",
            time_availability_hours_per_week=6,
            desired_outcome="Prove purge_all() actually empties a repository.",
            difficulty_target=DifficultyLevel.INTERMEDIATE,
        ),
        created_at=now,
        updated_at=now,
    )


@pytest.mark.parametrize(
    "database_name",
    ["pathai", "PathAI", "pathai_prod", "PATHAI_PROD", "prod", "PROD", "production", "Production"],
)
def test_denylist_refuses_regardless_of_case(database_name: str) -> None:
    with pytest.raises(reset_script.ResetRefused, match="denylist"):
        reset_script._check_not_denylisted(database_name)


def test_denylist_allows_a_non_denylisted_name() -> None:
    reset_script._check_not_denylisted("some_dev_db")  # does not raise


def test_denylist_runs_before_confirmation_check(monkeypatch: pytest.MonkeyPatch) -> None:
    """A denylisted name must refuse even if a confirmation token happens to match it."""
    monkeypatch.setenv(reset_script._CONFIRM_ENV_VAR, "pathai")

    with pytest.raises(reset_script.ResetRefused, match="denylist"):
        reset_script.run_safety_checks(database_name="pathai", repository_backend="mongo")


def test_confirmation_token_refuses_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(reset_script._CONFIRM_ENV_VAR, raising=False)

    with pytest.raises(reset_script.ResetRefused):
        reset_script._check_confirmation_token("some_dev_db")


def test_confirmation_token_refuses_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(reset_script._CONFIRM_ENV_VAR, "")

    with pytest.raises(reset_script.ResetRefused):
        reset_script._check_confirmation_token("some_dev_db")


def test_confirmation_token_refuses_when_mismatched(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(reset_script._CONFIRM_ENV_VAR, "not_the_right_name")

    with pytest.raises(reset_script.ResetRefused):
        reset_script._check_confirmation_token("some_dev_db")


def test_confirmation_token_passes_on_exact_match(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(reset_script._CONFIRM_ENV_VAR, "some_dev_db")

    reset_script._check_confirmation_token("some_dev_db")  # does not raise


def test_backend_guard_refuses_fake_backend() -> None:
    with pytest.raises(reset_script.ResetRefused, match="mongo"):
        reset_script._check_mongo_backend("fake")


def test_backend_guard_refuses_unrecognized_backend() -> None:
    with pytest.raises(reset_script.ResetRefused, match="mongo"):
        reset_script._check_mongo_backend("something_else")


def test_backend_guard_passes_for_mongo_backend() -> None:
    reset_script._check_mongo_backend("mongo")  # does not raise


def test_run_safety_checks_passes_when_all_three_checks_pass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(reset_script._CONFIRM_ENV_VAR, "some_dev_db")

    reset_script.run_safety_checks(
        database_name="some_dev_db",
        repository_backend="mongo",
    )  # does not raise


def test_purge_all_invokes_clear_on_every_one_of_the_thirteen_repositories(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(repository_backend="fake")
    repositories = build_repository_set(settings)

    assert len(reset_script.REPOSITORY_FIELD_NAMES) == 13

    called: list[str] = []
    for field_name in reset_script.REPOSITORY_FIELD_NAMES:
        repo = getattr(repositories, field_name)
        original_clear = repo.clear

        def spy(name: str = field_name, original: object = original_clear) -> None:
            called.append(name)
            original()  # type: ignore[operator]

        monkeypatch.setattr(repo, "clear", spy)

    cleared = reset_script.purge_all(repositories)

    assert cleared == list(reset_script.REPOSITORY_FIELD_NAMES)
    assert called == list(reset_script.REPOSITORY_FIELD_NAMES)


def test_purge_all_actually_empties_the_fake_repositories() -> None:
    """Behavioral check (not just spy counts): data really is gone after purge_all()."""
    settings = Settings(repository_backend="fake")
    repositories = build_repository_set(settings)
    repositories.goal.create(_sample_goal())

    assert repositories.goal.list_all() != []

    reset_script.purge_all(repositories)

    assert repositories.goal.list_all() == []


def _parsed_script_ast() -> ast.Module:
    source_path = Path(inspect.getfile(reset_script))
    return ast.parse(source_path.read_text(encoding="utf-8"))


def _imported_module_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def _called_function_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            names.add(node.func.id)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            names.add(node.func.attr)
    return names


def test_script_never_imports_canonical_demo_fixtures_or_calls_load_canonical_demo() -> None:
    tree = _parsed_script_ast()

    imports = _imported_module_names(tree)
    calls = _called_function_names(tree)

    assert not any("fixtures" in module or "canonical_demo" in module for module in imports)
    assert "load_canonical_demo" not in calls


def test_script_has_no_fastapi_import_or_route_wiring() -> None:
    tree = _parsed_script_ast()

    imports = _imported_module_names(tree)
    calls = _called_function_names(tree)

    assert not any("fastapi" in module.lower() for module in imports)
    assert "APIRouter" not in calls

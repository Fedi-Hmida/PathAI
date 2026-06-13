import pytest

from app.evaluation.constants import DEFAULT_EVALUATION_DATASET
from app.evaluation.datasets import get_dataset_summary, load_goal_fixtures
from app.evaluation.errors import EvaluationError


def test_evaluation_dataset_loads_five_synthetic_goals() -> None:
    fixtures = load_goal_fixtures()

    assert len(fixtures) >= 5
    assert {fixture.goal for fixture in fixtures} >= {
        "Learn RAG systems for graduation project.",
        "Learn NLP for internship.",
        "Learn computer vision basics.",
        "Learn MLOps deployment.",
        "Learn math foundations for AI.",
    }
    assert all(fixture.dataset_name == DEFAULT_EVALUATION_DATASET for fixture in fixtures)


def test_dataset_summary_describes_synthetic_scope() -> None:
    summary = get_dataset_summary()

    assert summary.dataset_name == DEFAULT_EVALUATION_DATASET
    assert summary.fixture_count >= 5
    assert "Synthetic" in summary.description


def test_unknown_dataset_raises_clear_error() -> None:
    with pytest.raises(EvaluationError) as exc_info:
        load_goal_fixtures("missing_dataset")

    assert exc_info.value.code == "evaluation_dataset_not_found"

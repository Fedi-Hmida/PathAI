from app.evaluation.datasets import load_goal_fixtures
from app.evaluation.metrics import (
    calculate_normalized_learning_gain,
    evaluate_assessment_fixture,
    evaluate_curriculum_fixture,
    evaluate_resource_fixture,
)


def test_normalized_learning_gain_calculation() -> None:
    result = calculate_normalized_learning_gain(40, 70, 100)

    assert result.raw_improvement == 30
    assert result.normalized_learning_gain == 0.5
    assert result.threshold_moved is True
    assert result.passed is True


def test_assessment_missing_topic_recall_penalizes_omissions() -> None:
    fixture = load_goal_fixtures()[0]
    result = evaluate_assessment_fixture(
        fixture,
        observed_missing_topics=fixture.expected_missing_topics[:-1],
    )

    assert result.expected_missing_topic_recall < 1.0
    assert any(metric.metric_name == "expected_missing_topic_recall" for metric in result.metrics)


def test_curriculum_metrics_capture_project_and_topic_coverage() -> None:
    fixture = load_goal_fixtures()[0]
    result = evaluate_curriculum_fixture(
        fixture,
        observed_topics=fixture.expected_topics[:2],
        has_project_week=False,
    )

    assert result.expected_topic_coverage < 1.0
    assert result.final_project_presence == 0.0


def test_resource_metrics_capture_coverage_and_fallback_rate() -> None:
    fixture = load_goal_fixtures()[0]
    result = evaluate_resource_fixture(
        fixture,
        resources_per_topic=1,
        source_types=["docs"],
        fallback_count=2,
    )

    assert result.minimum_resource_coverage < 1.0
    assert result.source_type_diversity < 1.0
    assert result.fallback_rate > 0.0

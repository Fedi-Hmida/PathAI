from app.evaluation.ablations import get_ablation_definitions
from app.evaluation.baselines import get_baseline_definitions
from app.evaluation.schemas import EvaluationRunRequest, LearningGainRequest
from app.evaluation.service import EvaluationService


def test_baseline_and_ablation_definitions_exist() -> None:
    baselines = get_baseline_definitions()
    ablations = get_ablation_definitions()

    assert {baseline.system_variant for baseline in baselines} >= {
        "static_expert",
        "single_agent_llm",
        "pathai_full",
    }
    assert {ablation.system_variant for ablation in ablations} == {
        "no_rag",
        "no_critic",
        "no_adapter",
    }


def test_service_runs_sample_evaluation_with_report_sections() -> None:
    service = EvaluationService()
    report = service.run_sample_evaluation(EvaluationRunRequest())

    assert report.dataset_summary.fixture_count >= 5
    assert report.assessment_results
    assert report.curriculum_results
    assert report.resource_results
    assert report.baseline_comparisons
    assert report.ablation_results
    assert report.rubrics
    assert "synthetic" in " ".join(report.limitations).lower()


def test_markdown_report_labels_synthetic_limitations() -> None:
    service = EvaluationService()
    report = service.run_sample_evaluation(EvaluationRunRequest())
    markdown = service.generate_markdown_report(report)

    assert "synthetic/offline" in markdown
    assert "does not prove real learner outcome improvement" in markdown
    assert "## Baselines" in markdown
    assert "## Ablations" in markdown


def test_service_learning_gain_uses_request_threshold() -> None:
    service = EvaluationService()
    result = service.calculate_learning_gain(
        LearningGainRequest(
            pre_test_score=20,
            post_test_score=55,
            max_score=100,
            pass_threshold=0.5,
        )
    )

    assert result.threshold_moved is True
    assert result.passed is True

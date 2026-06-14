from typing import Protocol

from app.evaluation.ablations import get_ablation_definitions
from app.evaluation.baselines import get_baseline_definitions
from app.evaluation.constants import DEFAULT_EVALUATION_DATASET, EvaluationSystemVariant
from app.evaluation.datasets import get_dataset_summary, list_dataset_summaries, load_goal_fixtures
from app.evaluation.metrics import (
    aggregate_metric_score,
    calculate_normalized_learning_gain,
    evaluate_adaptation_synthetic,
    evaluate_assessment_fixture,
    evaluate_critic_synthetic,
    evaluate_curriculum_fixture,
    evaluate_resource_fixture,
)
from app.evaluation.reports import report_to_markdown, summarize_report_metrics
from app.evaluation.rubrics import get_review_rubrics
from app.evaluation.schemas import (
    AblationResult,
    AdaptationEvaluationResult,
    AssessmentEvaluationResult,
    BaselineComparisonResult,
    CriticEvaluationResult,
    CurriculumEvaluationResult,
    EvaluationDatasetSummary,
    EvaluationReport,
    EvaluationRunRequest,
    LearnerGoalFixture,
    LearningGainRequest,
    LearningGainResult,
    MetricScore,
    ResourceRetrievalEvaluationResult,
    ReviewRubric,
)
from app.repositories import EvaluationRepository, FakeEvaluationRepository


class EvaluationStore(Protocol):
    def save(self, report: EvaluationReport) -> None:
        ...

    def list_reports(self, dataset_name: str | None = None) -> list[EvaluationReport]:
        ...

    def get(self, evaluation_id: str) -> EvaluationReport | None:
        ...

    def clear(self) -> None:
        ...


class RepositoryBackedEvaluationStore:
    def __init__(self, repository: EvaluationRepository | None = None) -> None:
        self.repository = repository or FakeEvaluationRepository()

    def save(self, report: EvaluationReport) -> None:
        self.repository.save_report(report.model_dump(mode="json"))

    def list_reports(self, dataset_name: str | None = None) -> list[EvaluationReport]:
        return [
            EvaluationReport.model_validate(payload)
            for payload in self.repository.list_reports(dataset_name)
        ]

    def get(self, evaluation_id: str) -> EvaluationReport | None:
        payload = self.repository.get_report(evaluation_id)
        if payload is None:
            return None
        return EvaluationReport.model_validate(payload)

    def clear(self) -> None:
        clear = getattr(self.repository, "clear", None)
        if callable(clear):
            clear()


class InMemoryEvaluationStore(RepositoryBackedEvaluationStore):
    """Backward-compatible fake repository store for tests and local demo routes."""

    def __init__(self) -> None:
        super().__init__(FakeEvaluationRepository())


class EvaluationService:
    def __init__(
        self,
        store: EvaluationStore | None = None,
        repository: EvaluationRepository | None = None,
    ) -> None:
        self.store = store or RepositoryBackedEvaluationStore(repository)

    def list_datasets(self) -> list[EvaluationDatasetSummary]:
        return list_dataset_summaries()

    def run_sample_evaluation(self, request: EvaluationRunRequest) -> EvaluationReport:
        fixtures = load_goal_fixtures(request.dataset_name)
        assessment_results = [
            self.evaluate_assessment_output(fixture.fixture_id) for fixture in fixtures
        ]
        curriculum_results = [
            self.evaluate_curriculum_output(fixture.fixture_id) for fixture in fixtures
        ]
        resource_results = [
            self.evaluate_resource_output(fixture.fixture_id) for fixture in fixtures
        ]
        critic_result = self.evaluate_critic_output()
        adaptation_result = self.evaluate_adaptation_output()
        learning_gain_results = [
            self.calculate_learning_gain(
                LearningGainRequest(
                    pre_test_score=fixture.pre_test_score,
                    post_test_score=fixture.post_test_score,
                    max_score=fixture.max_score,
                )
            )
            for fixture in fixtures
        ]
        metric_scores = _flatten_metric_scores(
            assessment_results=assessment_results,
            curriculum_results=curriculum_results,
            resource_results=resource_results,
            critic_result=critic_result,
            adaptation_result=adaptation_result,
            learning_gain_results=learning_gain_results,
        )
        report = EvaluationReport(
            dataset_name=request.dataset_name,
            system_variant=request.system_variant,
            dataset_summary=get_dataset_summary(request.dataset_name),
            assessment_results=assessment_results,
            curriculum_results=curriculum_results,
            resource_results=resource_results,
            critic_result=critic_result,
            adaptation_result=adaptation_result,
            learning_gain_results=learning_gain_results,
            baseline_comparisons=self.compare_baselines(request.system_variant, metric_scores),
            ablation_results=self.compare_ablations(metric_scores),
            rubrics=self.get_rubrics(),
            metric_scores=metric_scores,
            limitations=[
                "All metrics in this phase use synthetic fixtures and deterministic proxies.",
                "No real students, professors, or external LLM judges were used.",
                "Normalized learning gain is demonstrated from fixture scores only.",
            ],
        )
        strengths, weaknesses, recommendations = summarize_report_metrics(report)
        final_report = report.model_copy(
            update={
                "strengths": strengths,
                "weaknesses": weaknesses,
                "recommendations": recommendations,
            }
        )
        self.store.save(final_report)
        return final_report

    def evaluate_assessment_output(self, fixture_id: str) -> AssessmentEvaluationResult:
        fixture = _fixture_by_id(fixture_id)
        return evaluate_assessment_fixture(fixture)

    def evaluate_curriculum_output(self, fixture_id: str) -> CurriculumEvaluationResult:
        fixture = _fixture_by_id(fixture_id)
        return evaluate_curriculum_fixture(fixture)

    def evaluate_resource_output(self, fixture_id: str) -> ResourceRetrievalEvaluationResult:
        fixture = _fixture_by_id(fixture_id)
        return evaluate_resource_fixture(fixture)

    def evaluate_critic_output(self) -> CriticEvaluationResult:
        return evaluate_critic_synthetic()

    def evaluate_adaptation_output(self) -> AdaptationEvaluationResult:
        return evaluate_adaptation_synthetic()

    def calculate_learning_gain(self, request: LearningGainRequest) -> LearningGainResult:
        return calculate_normalized_learning_gain(
            pre_test_score=request.pre_test_score,
            post_test_score=request.post_test_score,
            max_score=request.max_score,
            pass_threshold=request.pass_threshold,
        )

    def compare_baselines(
        self,
        system_variant: EvaluationSystemVariant,
        metric_scores: list[MetricScore],
    ) -> list[BaselineComparisonResult]:
        current_score = aggregate_metric_score(metric_scores)
        synthetic_scores: dict[EvaluationSystemVariant, float] = {
            "static_expert": 0.58,
            "single_agent_llm": 0.63,
            "pathai_full": current_score,
            "no_rag": 0.72,
            "no_critic": 0.74,
            "no_adapter": 0.78,
        }
        results: list[BaselineComparisonResult] = []
        for baseline in get_baseline_definitions():
            score = synthetic_scores[baseline.system_variant]
            results.append(
                BaselineComparisonResult(
                    system_variant=system_variant,
                    baseline_type=baseline.system_variant,
                    score=score,
                    relative_note=(
                        "Synthetic structural comparison only; validate with expert review "
                        "before research claims."
                    ),
                    metrics=[
                        MetricScore(
                            category="baseline",
                            metric_name=f"{baseline.system_variant}_synthetic_score",
                            score=score,
                            passed=score >= 0.70,
                        )
                    ],
                )
            )
        return results

    def compare_ablations(self, metric_scores: list[MetricScore]) -> list[AblationResult]:
        current_score = aggregate_metric_score(metric_scores)
        synthetic_deltas: dict[EvaluationSystemVariant, float] = {
            "no_rag": -0.12,
            "no_critic": -0.09,
            "no_adapter": -0.06,
        }
        results: list[AblationResult] = []
        for ablation in get_ablation_definitions():
            delta = synthetic_deltas[ablation.system_variant]
            score = max(0.0, min(1.0, current_score + delta))
            results.append(
                AblationResult(
                    system_variant=ablation.system_variant,
                    removed_component=ablation.label.replace(" Ablation", ""),
                    expected_impact=ablation.limitations[0],
                    score_delta=delta,
                    metrics=[
                        MetricScore(
                            category="ablation",
                            metric_name=f"{ablation.system_variant}_synthetic_delta",
                            score=score,
                            passed=score >= 0.70,
                        )
                    ],
                )
            )
        return results

    def get_rubrics(self) -> list[ReviewRubric]:
        return get_review_rubrics()

    def generate_markdown_report(self, report: EvaluationReport) -> str:
        return report_to_markdown(report)

    def list_reports(self, dataset_name: str | None = None) -> list[EvaluationReport]:
        return self.store.list_reports(dataset_name)

    def get_report(self, evaluation_id: str) -> EvaluationReport | None:
        return self.store.get(evaluation_id)


def _fixture_by_id(fixture_id: str) -> LearnerGoalFixture:
    for fixture in load_goal_fixtures(DEFAULT_EVALUATION_DATASET):
        if fixture.fixture_id == fixture_id:
            return fixture
    fixture_ids = ", ".join(fixture.fixture_id for fixture in load_goal_fixtures())
    raise ValueError(f"Unknown evaluation fixture '{fixture_id}'. Available: {fixture_ids}.")


def _flatten_metric_scores(
    assessment_results: list[AssessmentEvaluationResult],
    curriculum_results: list[CurriculumEvaluationResult],
    resource_results: list[ResourceRetrievalEvaluationResult],
    critic_result: CriticEvaluationResult,
    adaptation_result: AdaptationEvaluationResult,
    learning_gain_results: list[LearningGainResult],
) -> list[MetricScore]:
    metrics: list[MetricScore] = []
    for assessment_result in assessment_results:
        metrics.extend(assessment_result.metrics)
    for curriculum_result in curriculum_results:
        metrics.extend(curriculum_result.metrics)
    for resource_result in resource_results:
        metrics.extend(resource_result.metrics)
    metrics.extend(critic_result.metrics)
    metrics.extend(adaptation_result.metrics)
    metrics.extend(
        MetricScore(
            category="learning_gain",
            metric_name="normalized_learning_gain",
            score=learning_gain.normalized_learning_gain,
            passed=learning_gain.normalized_learning_gain >= 0.30 or learning_gain.passed,
            issues=[]
            if learning_gain.normalized_learning_gain >= 0.30
            else ["Low synthetic gain."],
            recommendations=[]
            if learning_gain.normalized_learning_gain >= 0.30
            else ["Review assessment and curriculum fit for this fixture."],
        )
        for learning_gain in learning_gain_results
    )
    return metrics

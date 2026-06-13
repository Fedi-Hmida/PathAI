from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.evaluation.constants import (
    DEFAULT_EVALUATION_DATASET,
    DEFAULT_PASS_THRESHOLD,
    EvaluationSystemVariant,
    MetricCategory,
    RubricAudience,
    new_evaluation_id,
    utc_now,
)


class LearnerGoalFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fixture_id: str = Field(min_length=1, max_length=120)
    dataset_name: str = Field(default=DEFAULT_EVALUATION_DATASET, min_length=1)
    goal: str = Field(min_length=3, max_length=1000)
    timeline_weeks: int = Field(ge=1, le=52)
    hours_per_week: int = Field(ge=1, le=80)
    expected_topics: list[str] = Field(default_factory=list, min_length=1)
    expected_missing_topics: list[str] = Field(default_factory=list)
    expected_strong_topics: list[str] = Field(default_factory=list)
    expected_curriculum_themes: list[str] = Field(default_factory=list, min_length=1)
    expected_resource_topics: list[str] = Field(default_factory=list, min_length=1)
    pre_test_score: float = Field(ge=0.0)
    post_test_score: float = Field(ge=0.0)
    max_score: float = Field(default=100.0, gt=0.0)


class EvaluationDatasetSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_name: str
    description: str
    fixture_count: int = Field(ge=0)
    goals: list[str] = Field(default_factory=list)


class EvaluationDatasetsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    datasets: list[EvaluationDatasetSummary] = Field(default_factory=list)


class BaselineDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system_variant: EvaluationSystemVariant
    label: str = Field(min_length=1, max_length=180)
    description: str = Field(min_length=1, max_length=1000)
    expected_strengths: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    is_ablation: bool = False


class MetricScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: MetricCategory
    metric_name: str = Field(min_length=1, max_length=160)
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class AssessmentEvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fixture_id: str
    expected_missing_topic_recall: float = Field(ge=0.0, le=1.0)
    expected_strong_topic_precision: float = Field(ge=0.0, le=1.0)
    knowledge_map_coverage: float = Field(ge=0.0, le=1.0)
    confidence_calibration_placeholder: float = Field(ge=0.0, le=1.0)
    metrics: list[MetricScore] = Field(default_factory=list)


class CurriculumEvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fixture_id: str
    timeline_fit: float = Field(ge=0.0, le=1.0)
    weekly_hour_fit: float = Field(ge=0.0, le=1.0)
    expected_topic_coverage: float = Field(ge=0.0, le=1.0)
    weak_missing_topic_prioritization: float = Field(ge=0.0, le=1.0)
    final_project_presence: float = Field(ge=0.0, le=1.0)
    prerequisite_order_proxy: float = Field(ge=0.0, le=1.0)
    metrics: list[MetricScore] = Field(default_factory=list)


class ResourceRetrievalEvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fixture_id: str
    topic_match_rate: float = Field(ge=0.0, le=1.0)
    difficulty_fit_rate: float = Field(ge=0.0, le=1.0)
    minimum_resource_coverage: float = Field(ge=0.0, le=1.0)
    source_type_diversity: float = Field(ge=0.0, le=1.0)
    fallback_rate: float = Field(ge=0.0, le=1.0)
    metrics: list[MetricScore] = Field(default_factory=list)


class CriticEvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_detection_rate: float = Field(ge=0.0, le=1.0)
    false_approval_count: int = Field(ge=0)
    revision_instruction_usefulness_proxy: float = Field(ge=0.0, le=1.0)
    metrics: list[MetricScore] = Field(default_factory=list)


class AdaptationEvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trigger_correctness: float = Field(ge=0.0, le=1.0)
    no_trigger_correctness: float = Field(ge=0.0, le=1.0)
    affected_week_selection_quality: float = Field(ge=0.0, le=1.0)
    metrics: list[MetricScore] = Field(default_factory=list)


class LearningGainRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pre_test_score: float = Field(ge=0.0)
    post_test_score: float = Field(ge=0.0)
    max_score: float = Field(default=100.0, gt=0.0)
    pass_threshold: float = Field(default=DEFAULT_PASS_THRESHOLD, ge=0.0, le=1.0)


class LearningGainResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pre_test_score: float = Field(ge=0.0)
    post_test_score: float = Field(ge=0.0)
    max_score: float = Field(gt=0.0)
    raw_improvement: float
    normalized_learning_gain: float = Field(ge=0.0, le=1.0)
    threshold_moved: bool
    passed: bool


class BaselineComparisonResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system_variant: EvaluationSystemVariant
    baseline_type: EvaluationSystemVariant
    score: float = Field(ge=0.0, le=1.0)
    relative_note: str = Field(min_length=1, max_length=700)
    metrics: list[MetricScore] = Field(default_factory=list)


class AblationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system_variant: EvaluationSystemVariant
    removed_component: str = Field(min_length=1, max_length=120)
    expected_impact: str = Field(min_length=1, max_length=700)
    score_delta: float = Field(ge=-1.0, le=1.0)
    metrics: list[MetricScore] = Field(default_factory=list)


class RubricCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion: str = Field(min_length=1, max_length=180)
    scale_description: str = Field(min_length=1, max_length=800)
    high_score_anchor: str = Field(min_length=1, max_length=500)
    low_score_anchor: str = Field(min_length=1, max_length=500)


class ReviewRubric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rubric_id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=180)
    audience: RubricAudience
    scale: str = Field(default="1-5")
    criteria: list[RubricCriterion] = Field(default_factory=list, min_length=1)
    reviewer_notes_field: bool = True


class EvaluationRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_name: str = Field(default=DEFAULT_EVALUATION_DATASET, min_length=1)
    system_variant: EvaluationSystemVariant = "pathai_full"


class EvaluationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evaluation_id: str = Field(default_factory=new_evaluation_id)
    dataset_name: str
    system_variant: EvaluationSystemVariant
    dataset_summary: EvaluationDatasetSummary
    assessment_results: list[AssessmentEvaluationResult] = Field(default_factory=list)
    curriculum_results: list[CurriculumEvaluationResult] = Field(default_factory=list)
    resource_results: list[ResourceRetrievalEvaluationResult] = Field(default_factory=list)
    critic_result: CriticEvaluationResult
    adaptation_result: AdaptationEvaluationResult
    learning_gain_results: list[LearningGainResult] = Field(default_factory=list)
    baseline_comparisons: list[BaselineComparisonResult] = Field(default_factory=list)
    ablation_results: list[AblationResult] = Field(default_factory=list)
    rubrics: list[ReviewRubric] = Field(default_factory=list)
    metric_scores: list[MetricScore] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class EvaluationRubricsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rubrics: list[ReviewRubric] = Field(default_factory=list)


class MarkdownReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report: EvaluationReport
    markdown: str = Field(min_length=1)

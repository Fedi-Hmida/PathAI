from collections.abc import Sequence
from re import findall

from app.evaluation.constants import (
    DEFAULT_MIN_RESOURCE_COVERAGE,
    DEFAULT_PASS_THRESHOLD,
    MetricCategory,
)
from app.evaluation.schemas import (
    AdaptationEvaluationResult,
    AssessmentEvaluationResult,
    CriticEvaluationResult,
    CurriculumEvaluationResult,
    LearnerGoalFixture,
    LearningGainResult,
    MetricScore,
    ResourceRetrievalEvaluationResult,
)


def calculate_normalized_learning_gain(
    pre_test_score: float,
    post_test_score: float,
    max_score: float = 100.0,
    pass_threshold: float = DEFAULT_PASS_THRESHOLD,
) -> LearningGainResult:
    capped_pre = _clamp(pre_test_score, 0.0, max_score)
    capped_post = _clamp(post_test_score, 0.0, max_score)
    denominator = max_score - capped_pre
    normalized = 0.0 if denominator <= 0 else _clamp((capped_post - capped_pre) / denominator)
    threshold_score = max_score * pass_threshold
    return LearningGainResult(
        pre_test_score=capped_pre,
        post_test_score=capped_post,
        max_score=max_score,
        raw_improvement=capped_post - capped_pre,
        normalized_learning_gain=normalized,
        threshold_moved=capped_pre < threshold_score <= capped_post,
        passed=capped_post >= threshold_score,
    )


def evaluate_assessment_fixture(
    fixture: LearnerGoalFixture,
    observed_missing_topics: Sequence[str] | None = None,
    observed_strong_topics: Sequence[str] | None = None,
    confidence_score: float = 0.82,
) -> AssessmentEvaluationResult:
    missing_recall = overlap_recall(
        fixture.expected_missing_topics,
        observed_missing_topics or fixture.expected_missing_topics,
    )
    strong_precision = overlap_precision(
        fixture.expected_strong_topics,
        observed_strong_topics or fixture.expected_strong_topics,
    )
    coverage = overlap_recall(
        fixture.expected_topics,
        [
            *(observed_missing_topics or fixture.expected_missing_topics),
            *(observed_strong_topics or fixture.expected_strong_topics),
        ],
    )
    confidence_alignment = 1.0 - abs(_clamp(confidence_score) - coverage)
    metrics = [
        _metric("assessment", "expected_missing_topic_recall", missing_recall),
        _metric("assessment", "expected_strong_topic_precision", strong_precision),
        _metric("assessment", "knowledge_map_coverage", coverage),
        _metric("assessment", "confidence_calibration_placeholder", confidence_alignment),
    ]
    return AssessmentEvaluationResult(
        fixture_id=fixture.fixture_id,
        expected_missing_topic_recall=missing_recall,
        expected_strong_topic_precision=strong_precision,
        knowledge_map_coverage=coverage,
        confidence_calibration_placeholder=confidence_alignment,
        metrics=metrics,
    )


def evaluate_curriculum_fixture(
    fixture: LearnerGoalFixture,
    observed_topics: Sequence[str] | None = None,
    timeline_weeks: int | None = None,
    hours_per_week: int | None = None,
    has_project_week: bool = True,
) -> CurriculumEvaluationResult:
    timeline_fit = (
        1.0 if (timeline_weeks or fixture.timeline_weeks) == fixture.timeline_weeks else 0.0
    )
    weekly_hour_fit = (
        1.0 if (hours_per_week or fixture.hours_per_week) <= fixture.hours_per_week else 0.0
    )
    topic_coverage = overlap_recall(
        fixture.expected_topics,
        observed_topics or fixture.expected_topics,
    )
    weak_missing_priority = overlap_recall(
        fixture.expected_missing_topics,
        observed_topics or fixture.expected_missing_topics,
    )
    final_project_presence = 1.0 if has_project_week else 0.0
    prerequisite_proxy = min(1.0, (timeline_fit + topic_coverage + final_project_presence) / 3.0)
    metrics = [
        _metric("curriculum", "timeline_fit", timeline_fit),
        _metric("curriculum", "weekly_hour_fit", weekly_hour_fit),
        _metric("curriculum", "expected_topic_coverage", topic_coverage),
        _metric("curriculum", "weak_missing_topic_prioritization", weak_missing_priority),
        _metric("curriculum", "final_project_application_presence", final_project_presence),
        _metric("curriculum", "prerequisite_order_proxy", prerequisite_proxy),
    ]
    return CurriculumEvaluationResult(
        fixture_id=fixture.fixture_id,
        timeline_fit=timeline_fit,
        weekly_hour_fit=weekly_hour_fit,
        expected_topic_coverage=topic_coverage,
        weak_missing_topic_prioritization=weak_missing_priority,
        final_project_presence=final_project_presence,
        prerequisite_order_proxy=prerequisite_proxy,
        metrics=metrics,
    )


def evaluate_resource_fixture(
    fixture: LearnerGoalFixture,
    observed_resource_topics: Sequence[str] | None = None,
    difficulty_fit_rate: float = 0.9,
    resources_per_topic: int = DEFAULT_MIN_RESOURCE_COVERAGE,
    source_types: Sequence[str] | None = None,
    fallback_count: int = 0,
) -> ResourceRetrievalEvaluationResult:
    topics = observed_resource_topics or fixture.expected_resource_topics
    topic_match_rate = overlap_recall(fixture.expected_resource_topics, topics)
    coverage = (
        1.0
        if resources_per_topic >= DEFAULT_MIN_RESOURCE_COVERAGE
        else resources_per_topic / DEFAULT_MIN_RESOURCE_COVERAGE
    )
    types = set(source_types or ["docs", "article", "video"])
    diversity = min(1.0, len(types) / 3.0)
    total_results = max(1, len(topics) * max(1, resources_per_topic))
    fallback_rate = _clamp(fallback_count / total_results)
    metrics = [
        _metric("resources", "topic_match_rate", topic_match_rate),
        _metric("resources", "difficulty_fit_rate", difficulty_fit_rate),
        _metric("resources", "minimum_resource_coverage", coverage),
        _metric("resources", "source_type_diversity", diversity),
        _metric("resources", "low_fallback_rate", 1.0 - fallback_rate),
    ]
    return ResourceRetrievalEvaluationResult(
        fixture_id=fixture.fixture_id,
        topic_match_rate=topic_match_rate,
        difficulty_fit_rate=_clamp(difficulty_fit_rate),
        minimum_resource_coverage=_clamp(coverage),
        source_type_diversity=diversity,
        fallback_rate=fallback_rate,
        metrics=metrics,
    )


def evaluate_critic_synthetic(
    issue_detection_rate: float = 0.88,
    false_approval_count: int = 0,
    revision_instruction_usefulness: float = 0.82,
) -> CriticEvaluationResult:
    false_approval_score = 1.0 if false_approval_count == 0 else 0.0
    metrics = [
        _metric("critic", "seeded_issue_detection_rate", issue_detection_rate),
        _metric("critic", "false_approval_avoidance", false_approval_score),
        _metric("critic", "revision_instruction_usefulness_proxy", revision_instruction_usefulness),
    ]
    return CriticEvaluationResult(
        issue_detection_rate=_clamp(issue_detection_rate),
        false_approval_count=false_approval_count,
        revision_instruction_usefulness_proxy=_clamp(revision_instruction_usefulness),
        metrics=metrics,
    )


def evaluate_adaptation_synthetic(
    trigger_correctness: float = 0.86,
    no_trigger_correctness: float = 0.9,
    affected_week_selection_quality: float = 0.84,
) -> AdaptationEvaluationResult:
    metrics = [
        _metric("adaptation", "trigger_correctness", trigger_correctness),
        _metric("adaptation", "no_trigger_correctness", no_trigger_correctness),
        _metric("adaptation", "affected_week_selection_quality", affected_week_selection_quality),
    ]
    return AdaptationEvaluationResult(
        trigger_correctness=_clamp(trigger_correctness),
        no_trigger_correctness=_clamp(no_trigger_correctness),
        affected_week_selection_quality=_clamp(affected_week_selection_quality),
        metrics=metrics,
    )


def aggregate_metric_score(metrics: Sequence[MetricScore]) -> float:
    if not metrics:
        return 0.0
    return sum(metric.score for metric in metrics) / len(metrics)


def overlap_recall(expected: Sequence[str], observed: Sequence[str]) -> float:
    expected_tokens = {_normalize(value) for value in expected if _normalize(value)}
    observed_tokens = {_normalize(value) for value in observed if _normalize(value)}
    if not expected_tokens:
        return 1.0
    return len(expected_tokens & observed_tokens) / len(expected_tokens)


def overlap_precision(expected: Sequence[str], observed: Sequence[str]) -> float:
    expected_tokens = {_normalize(value) for value in expected if _normalize(value)}
    observed_tokens = {_normalize(value) for value in observed if _normalize(value)}
    if not observed_tokens:
        return 1.0 if not expected_tokens else 0.0
    return len(expected_tokens & observed_tokens) / len(observed_tokens)


def _metric(category: MetricCategory, name: str, score: float) -> MetricScore:
    normalized = _clamp(score)
    return MetricScore(
        category=category,
        metric_name=name,
        score=normalized,
        passed=normalized >= DEFAULT_PASS_THRESHOLD,
        issues=[] if normalized >= DEFAULT_PASS_THRESHOLD else [f"{name} is below threshold."],
        recommendations=[]
        if normalized >= DEFAULT_PASS_THRESHOLD
        else [f"Review the {category} stage for {name} failures."],
    )


def _normalize(value: str) -> str:
    return " ".join(findall(r"[a-z0-9]+", value.lower()))


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))

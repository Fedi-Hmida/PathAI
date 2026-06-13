from app.evaluation.metrics import aggregate_metric_score
from app.evaluation.schemas import EvaluationReport, MetricScore


def summarize_report_metrics(report: EvaluationReport) -> tuple[list[str], list[str], list[str]]:
    average = aggregate_metric_score(report.metric_scores)
    strengths: list[str] = []
    weaknesses: list[str] = []
    recommendations: list[str] = []

    if average >= 0.80:
        strengths.append("Synthetic evaluation indicates strong structural coverage.")
    else:
        weaknesses.append("Synthetic evaluation indicates uneven structural coverage.")

    weak_metrics = [metric for metric in report.metric_scores if not metric.passed]
    if weak_metrics:
        weaknesses.extend(
            f"{metric.category}:{metric.metric_name} scored {metric.score:.2f}."
            for metric in weak_metrics[:5]
        )
        recommendations.append("Inspect failing synthetic metrics before claiming system quality.")
    else:
        strengths.append("All synthetic metric checks met the configured threshold.")

    recommendations.append(
        "Run expert review and a real pre-test/post-test study before making "
        "learning-outcome claims."
    )
    return strengths, weaknesses, recommendations


def metric_summary(metrics: list[MetricScore]) -> str:
    if not metrics:
        return "No metrics were produced."
    average = aggregate_metric_score(metrics)
    passed = sum(1 for metric in metrics if metric.passed)
    return f"{passed}/{len(metrics)} metrics passed; average synthetic score {average:.2f}."


def report_to_markdown(report: EvaluationReport) -> str:
    lines = [
        f"# PathAI Evaluation Report - {report.evaluation_id}",
        "",
        "## Scope",
        f"- Dataset: `{report.dataset_name}`",
        f"- System variant: `{report.system_variant}`",
        "- Evaluation type: synthetic/offline engineering evaluation.",
        "- This report does not prove real learner outcome improvement.",
        "",
        "## Dataset Summary",
        f"- Fixtures: {report.dataset_summary.fixture_count}",
        f"- Goals: {', '.join(report.dataset_summary.goals)}",
        "",
        "## Metric Summary",
        metric_summary(report.metric_scores),
        "",
        "## Baselines",
    ]
    lines.extend(
        f"- `{comparison.baseline_type}`: {comparison.score:.2f} - {comparison.relative_note}"
        for comparison in report.baseline_comparisons
    )
    lines.extend(["", "## Ablations"])
    lines.extend(
        f"- `{ablation.system_variant}` removes {ablation.removed_component}: "
        f"delta {ablation.score_delta:.2f}"
        for ablation in report.ablation_results
    )
    lines.extend(["", "## Strengths"])
    lines.extend(f"- {item}" for item in report.strengths)
    lines.extend(["", "## Weaknesses"])
    lines.extend(f"- {item}" for item in report.weaknesses)
    lines.extend(["", "## Recommendations"])
    lines.extend(f"- {item}" for item in report.recommendations)
    lines.extend(["", "## Limitations"])
    lines.extend(f"- {item}" for item in report.limitations)
    return "\n".join(lines)

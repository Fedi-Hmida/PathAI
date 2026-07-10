from __future__ import annotations

from app.fixtures import canonical_demo as demo
from app.repositories.mongo.base import from_document, to_document
from app.schemas.evaluation import EvaluationReportDTO


def test_evaluation_report_document_round_trip_with_embedded_metric_scores() -> None:
    evaluation_report = demo.EVALUATION_REPORT
    document = to_document(evaluation_report, evaluation_report.evaluation_report_id)

    assert document["_id"] == evaluation_report.evaluation_report_id
    assert document["pass_status"] == evaluation_report.pass_status.value
    assert isinstance(document["metric_scores"], dict)
    coverage = evaluation_report.metric_scores.curriculum_coverage
    assert document["metric_scores"]["curriculum_coverage"] == coverage

    restored = from_document(document, EvaluationReportDTO)
    assert restored == evaluation_report

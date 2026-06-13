from app.agents.state import GraphState
from app.progress.schemas import CurriculumProgressSummary


def apply_progress_summary_to_graph_state(
    state: GraphState,
    summary: CurriculumProgressSummary,
) -> GraphState:
    progress_payload = {
        "curriculum_id": summary.curriculum_id,
        "completion_percentage": summary.analytics.completion_percentage,
        "stuck_topic_count": summary.analytics.stuck_topic_count,
        "average_quiz_score": summary.analytics.average_quiz_score,
        "signals": [
            signal.model_dump(mode="json") for signal in summary.analytics.signals
        ],
    }
    return state.model_copy(
        update={
            "progress": [progress_payload],
            "metadata": {
                **state.metadata,
                "progress_curriculum_id": summary.curriculum_id,
                "progress_signal_count": len(summary.analytics.signals),
            },
        },
        deep=True,
    )

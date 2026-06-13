from app.adapter.schemas import AdaptationResult
from app.agents.state import GraphState


def apply_adaptation_result_to_graph_state(
    state: GraphState,
    result: AdaptationResult,
) -> GraphState:
    progress_payloads = [
        {
            "type": "adaptation_signal",
            "reason": signal.reason,
            "severity": signal.severity,
            "message": signal.message,
            "week_number": signal.week_number,
            "topic_id": signal.topic_id,
        }
        for signal in result.decision.signals
    ]
    return state.model_copy(
        update={
            "progress": [*state.progress, *progress_payloads],
            "curriculum": [
                week.model_dump(mode="json")
                for week in (result.curriculum_after or result.curriculum_before).weeks
            ],
            "metadata": {
                **state.metadata,
                "adaptation_id": result.adaptation_id,
                "adaptation_trigger_reason": result.decision.trigger_reason,
                "adaptation_should_replan": result.decision.should_replan,
                "adaptation_critic_approved": result.critic_review.approved
                if result.critic_review
                else None,
            },
        },
        deep=True,
    )

from app.agents.state import GraphState
from app.quiz.schemas import QuizResult


def append_quiz_result_to_graph_progress(
    state: GraphState,
    result: QuizResult,
) -> GraphState:
    payload = {
        "type": "quiz_result",
        "quiz_id": result.quiz_id,
        "curriculum_id": result.curriculum_id,
        "week_number": result.week_number,
        "score": result.score,
        "passed": result.passed,
        "low_score_signal": result.low_score_signal,
    }
    return state.model_copy(
        update={
            "progress": [*state.progress, payload],
            "metadata": {
                **state.metadata,
                "latest_quiz_score": result.score,
                "latest_quiz_low_score": result.low_score_signal,
            },
        },
        deep=True,
    )

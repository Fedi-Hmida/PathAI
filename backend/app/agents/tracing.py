from app.agents.constants import TraceStatus
from app.agents.state import GraphError, GraphState, GraphWarning, TraceEvent, utc_now


def record_trace(
    state: GraphState,
    node_name: str,
    status: TraceStatus,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> GraphState:
    next_state = state.model_copy(deep=True)
    next_state.trace.append(
        TraceEvent(
            node_name=node_name,
            status=status,
            revision_count=next_state.revision_count,
            warnings=warnings or [],
            errors=errors or [],
        )
    )
    next_state.updated_at = utc_now()
    return next_state


def add_warning(state: GraphState, node_name: str, code: str, message: str) -> GraphState:
    next_state = state.model_copy(deep=True)
    next_state.warnings.append(GraphWarning(node_name=node_name, code=code, message=message))
    next_state.updated_at = utc_now()
    return next_state


def add_error(
    state: GraphState,
    node_name: str,
    code: str,
    message: str,
    recoverable: bool = True,
) -> GraphState:
    next_state = state.model_copy(deep=True)
    next_state.errors.append(
        GraphError(
            node_name=node_name,
            code=code,
            message=message,
            recoverable=recoverable,
        )
    )
    next_state.updated_at = utc_now()
    return next_state

class GraphExecutionError(Exception):
    """Raised when deterministic graph execution cannot continue safely."""


class LangGraphDependencyError(GraphExecutionError):
    """Raised when LangGraph is required but not installed."""


class CheckpointNotFoundError(GraphExecutionError):
    """Raised when a graph checkpoint cannot be found."""

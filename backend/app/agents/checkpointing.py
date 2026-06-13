from dataclasses import dataclass
from typing import Protocol

from app.agents.errors import CheckpointNotFoundError
from app.agents.state import GraphState, utc_now


@dataclass(frozen=True)
class CheckpointRecord:
    run_id: str
    sequence: int
    state: GraphState


class CheckpointStore(Protocol):
    def save(self, state: GraphState) -> CheckpointRecord:
        ...

    def load_latest(self, run_id: str) -> GraphState:
        ...

    def list_for_run(self, run_id: str) -> list[CheckpointRecord]:
        ...


class InMemoryCheckpointStore:
    def __init__(self) -> None:
        self._records: dict[str, list[CheckpointRecord]] = {}

    def save(self, state: GraphState) -> CheckpointRecord:
        snapshot = state.model_copy(deep=True)
        snapshot.updated_at = utc_now()
        records = self._records.setdefault(snapshot.run_id, [])
        record = CheckpointRecord(
            run_id=snapshot.run_id,
            sequence=len(records) + 1,
            state=snapshot,
        )
        records.append(record)
        return record

    def load_latest(self, run_id: str) -> GraphState:
        records = self._records.get(run_id, [])
        if not records:
            raise CheckpointNotFoundError(f"No checkpoint found for run_id={run_id}.")
        return records[-1].state.model_copy(deep=True)

    def list_for_run(self, run_id: str) -> list[CheckpointRecord]:
        return list(self._records.get(run_id, []))

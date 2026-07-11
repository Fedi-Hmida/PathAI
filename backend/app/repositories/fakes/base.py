from __future__ import annotations

from typing import Any, Generic, TypeVar, cast

from pydantic import BaseModel

from app.repositories.errors import DuplicateRecordError, NotFoundError

ModelT = TypeVar("ModelT", bound=BaseModel)


class InMemoryStore(Generic[ModelT]):
    def __init__(self, entity_name: str) -> None:
        self._entity_name = entity_name
        self._records: dict[str, ModelT] = {}

    def create(self, record_id: str, record: ModelT) -> ModelT:
        if record_id in self._records:
            msg = f"{self._entity_name} already exists: {record_id}"
            raise DuplicateRecordError(msg)
        self._records[record_id] = self._copy(record)
        return self._copy(record)

    def save(self, record_id: str, record: ModelT) -> ModelT:
        self._require_exists(record_id)
        self._records[record_id] = self._copy(record)
        return self._copy(record)

    def get(self, record_id: str) -> ModelT:
        self._require_exists(record_id)
        return self._copy(self._records[record_id])

    def list_all(self) -> list[ModelT]:
        return [self._copy(record) for record in self._records.values()]

    def list_where(self, field_name: str, expected: object) -> list[ModelT]:
        return [
            self._copy(record)
            for record in self._records.values()
            if getattr(record, field_name, None) == expected
        ]

    def get_where(self, field_name: str, expected: object) -> ModelT:
        matches = self.list_where(field_name, expected)
        if not matches:
            msg = f"{self._entity_name} not found for {field_name}: {expected}"
            raise NotFoundError(msg)
        return matches[0]

    def update_fields(self, record_id: str, **changes: Any) -> ModelT:
        self._require_exists(record_id)
        updated = self._records[record_id].model_copy(update=changes, deep=True)
        self._records[record_id] = self._copy(cast(ModelT, updated))
        return self._copy(self._records[record_id])

    def delete(self, record_id: str) -> None:
        """Remove a record if present. Idempotent: absent IDs are a no-op."""
        self._records.pop(record_id, None)

    def clear(self) -> None:
        self._records.clear()

    def _require_exists(self, record_id: str) -> None:
        if record_id not in self._records:
            msg = f"{self._entity_name} not found: {record_id}"
            raise NotFoundError(msg)

    @staticmethod
    def _copy(record: ModelT) -> ModelT:
        return cast(ModelT, record.model_copy(deep=True))

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from app.repositories.errors import DuplicateRecordError, NotFoundError

ModelT = TypeVar("ModelT", bound=BaseModel)


def to_document(record: BaseModel, record_id: str) -> dict[str, Any]:
    document = record.model_dump(mode="json")
    document["_id"] = record_id
    return document


def from_document(document: dict[str, Any], model: type[ModelT]) -> ModelT:
    payload = {key: value for key, value in document.items() if key != "_id"}
    return model.model_validate(payload)


class MongoStore(Generic[ModelT]):
    def __init__(
        self,
        collection: Collection[dict[str, Any]],
        model: type[ModelT],
        entity_name: str,
    ) -> None:
        self._collection = collection
        self._model = model
        self._entity_name = entity_name

    def create(self, record_id: str, record: ModelT) -> ModelT:
        try:
            self._collection.insert_one(to_document(record, record_id))
        except DuplicateKeyError as exc:
            msg = f"{self._entity_name} already exists: {record_id}"
            raise DuplicateRecordError(msg) from exc
        return self.get(record_id)

    def save(self, record_id: str, record: ModelT) -> ModelT:
        self._require_exists(record_id)
        self._collection.replace_one({"_id": record_id}, to_document(record, record_id))
        return self.get(record_id)

    def get(self, record_id: str) -> ModelT:
        document = self._collection.find_one({"_id": record_id})
        if document is None:
            msg = f"{self._entity_name} not found: {record_id}"
            raise NotFoundError(msg)
        return from_document(document, self._model)

    def list_all(self) -> list[ModelT]:
        return [from_document(doc, self._model) for doc in self._collection.find({})]

    def list_where(self, field_name: str, expected: object) -> list[ModelT]:
        documents = self._collection.find({field_name: expected})
        return [from_document(doc, self._model) for doc in documents]

    def get_where(self, field_name: str, expected: object) -> ModelT:
        matches = self.list_where(field_name, expected)
        if not matches:
            msg = f"{self._entity_name} not found for {field_name}: {expected}"
            raise NotFoundError(msg)
        return matches[0]

    def update_fields(self, record_id: str, **changes: Any) -> ModelT:
        current = self.get(record_id)
        updated = current.model_copy(update=changes, deep=True)
        return self.save(record_id, updated)

    def delete(self, record_id: str) -> None:
        """Remove a record if present. Idempotent: absent IDs are a no-op."""
        self._collection.delete_one({"_id": record_id})

    def clear(self) -> None:
        self._collection.delete_many({})

    def _require_exists(self, record_id: str) -> None:
        if self._collection.find_one({"_id": record_id}) is None:
            msg = f"{self._entity_name} not found: {record_id}"
            raise NotFoundError(msg)

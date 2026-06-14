from collections.abc import Mapping
from typing import Any, Protocol

from app.curriculum.schemas import CurriculumPlan, CurriculumTopic
from app.rag.constants import (
    resource_approved_path,
    resource_staging_path,
)
from app.rag.curation import (
    build_catalog_items_from_seeds,
    canonical_resource_directories,
    load_canonical_resource_seeds,
    load_resource_schema,
    validate_seed_payload,
)
from app.rag.errors import ResourceCatalogError, ResourceSeedError
from app.rag.reranker import DeterministicResourceReranker
from app.rag.retriever import ResourceRetriever
from app.rag.schemas import (
    CurriculumResourceAttachmentRequest,
    CurriculumResourceAttachmentResponse,
    ResourceCandidate,
    ResourceCatalogItem,
    ResourceCatalogSummary,
    ResourceReferencePayload,
    ResourceRerankRequest,
    ResourceRetrievalRequest,
    ResourceRetrievalResult,
    ResourceSeedValidationResponse,
    TopicResourceAttachment,
)
from app.repositories import FakeResourceRepository, ResourceRepository


class ResourceCatalog:
    def __init__(self, items: list[ResourceCatalogItem] | None = None) -> None:
        self._items = {item.resource_id: item for item in items or []}

    @property
    def items(self) -> list[ResourceCatalogItem]:
        return list(self._items.values())

    def count(self) -> int:
        return len(self._items)

    def summary(self) -> ResourceCatalogSummary:
        items = self.items
        return ResourceCatalogSummary(
            total_resources=len(items),
            topics=sorted({topic for item in items for topic in item.topics}),
            difficulties=sorted({item.difficulty for item in items}),
            resource_types=sorted({item.type for item in items}),
            sources=sorted({item.source_name for item in items}),
            canonical_paths=[str(resource_staging_path()), str(resource_approved_path())],
        )


class ResourceStore(Protocol):
    def save_catalog(self, items: list[ResourceCatalogItem]) -> None:
        ...

    def load_catalog(self) -> list[ResourceCatalogItem]:
        ...

    def save_attachment(self, attachment: CurriculumResourceAttachmentResponse) -> None:
        ...

    def load_attachment(
        self,
        curriculum_id: str,
    ) -> CurriculumResourceAttachmentResponse | None:
        ...

    def clear(self) -> None:
        ...


class RepositoryBackedResourceStore:
    def __init__(self, repository: ResourceRepository | None = None) -> None:
        self.repository = repository or FakeResourceRepository()

    def save_catalog(self, items: list[ResourceCatalogItem]) -> None:
        for item in items:
            self.repository.upsert_resource(item.model_dump(mode="json"))

    def load_catalog(self) -> list[ResourceCatalogItem]:
        return [
            ResourceCatalogItem.model_validate(payload)
            for payload in self.repository.list_catalog()
        ]

    def save_attachment(self, attachment: CurriculumResourceAttachmentResponse) -> None:
        self.repository.save_attachment(attachment.model_dump(mode="json"))

    def load_attachment(
        self,
        curriculum_id: str,
    ) -> CurriculumResourceAttachmentResponse | None:
        payload = self.repository.get_attachment_for_curriculum(curriculum_id)
        if payload is None:
            return None
        return CurriculumResourceAttachmentResponse.model_validate(payload)

    def clear(self) -> None:
        clear = getattr(self.repository, "clear", None)
        if callable(clear):
            clear()


class InMemoryResourceStore(RepositoryBackedResourceStore):
    """Backward-compatible fake repository store for tests and local demo routes."""

    def __init__(self) -> None:
        super().__init__(FakeResourceRepository())


class ResourceService:
    def __init__(
        self,
        catalog: ResourceCatalog | None = None,
        store: ResourceStore | None = None,
        repository: ResourceRepository | None = None,
    ) -> None:
        self._catalog = catalog
        self.store = store or RepositoryBackedResourceStore(repository)
        if catalog is not None:
            self.store.save_catalog(catalog.items)

    def load_catalog_from_canonical_paths(
        self,
        include_staging: bool = True,
        include_approved: bool = True,
    ) -> ResourceCatalog:
        try:
            seeds = load_canonical_resource_seeds(
                include_staging=include_staging,
                include_approved=include_approved,
            )
        except Exception as exc:
            raise ResourceCatalogError(
                code="resource_catalog_load_failed",
                message="Failed to load curated resource catalog.",
                status_code=500,
                details={"error": str(exc)},
            ) from exc
        catalog = ResourceCatalog(build_catalog_items_from_seeds(seeds))
        self._catalog = catalog
        self.store.save_catalog(catalog.items)
        return catalog

    def get_catalog(self) -> ResourceCatalog:
        if self._catalog is None:
            items = self.store.load_catalog()
            self._catalog = ResourceCatalog(items) if items else None
        if self._catalog is None:
            self.load_catalog_from_canonical_paths()
        if self._catalog is None:
            raise ResourceCatalogError(
                code="resource_catalog_unavailable",
                message="Resource catalog is unavailable.",
                status_code=500,
            )
        return self._catalog

    def get_resource_catalog_summary(self) -> ResourceCatalogSummary:
        return self.get_catalog().summary()

    def validate_seed(self, payload: Mapping[str, Any]) -> ResourceSeedValidationResponse:
        try:
            return validate_seed_payload(payload, load_resource_schema())
        except Exception as exc:
            raise ResourceSeedError(
                code="resource_seed_invalid",
                message=str(exc),
                status_code=422,
            ) from exc

    def retrieve_for_topic(
        self,
        request: ResourceRetrievalRequest,
    ) -> ResourceRetrievalResult:
        catalog = self.get_catalog()
        retriever = ResourceRetriever(catalog.items)
        initial = retriever.retrieve(request)
        rerank_request = ResourceRerankRequest(
            goal=request.goal,
            topic=request.topic,
            difficulty=request.difficulty,
            knowledge_map=request.knowledge_map,
            candidates=initial.candidates,
            top_k=request.top_k,
        )
        reranked = DeterministicResourceReranker().rerank(rerank_request)
        by_id = {candidate.resource.resource_id: candidate for candidate in initial.candidates}
        ordered = [
            by_id[ranked.resource_id]
            for ranked in reranked.ranked_candidates
            if ranked.resource_id in by_id
        ]
        return initial.model_copy(update={"candidates": ordered})

    def retrieve_for_curriculum(
        self,
        request: CurriculumResourceAttachmentRequest,
    ) -> CurriculumResourceAttachmentResponse:
        topic_results: list[ResourceRetrievalResult] = []
        attachments: list[TopicResourceAttachment] = []
        warnings: list[str] = []
        for week in request.curriculum.weeks:
            for topic in week.topics:
                retrieval_request = _request_from_curriculum_topic(
                    curriculum=request.curriculum,
                    topic=topic,
                    top_k=request.top_k,
                    include_foundational_fallback=request.include_foundational_fallback,
                )
                result = self.retrieve_for_topic(retrieval_request)
                topic_results.append(result)
                if result.warnings:
                    warnings.extend(result.warnings)
                attachments.append(
                    TopicResourceAttachment(
                        topic_id=topic.topic_id,
                        topic=topic.title,
                        resources=[
                            candidate_to_reference(candidate) for candidate in result.candidates
                        ],
                        warnings=result.warnings,
                    )
                )

        enriched = attach_resources_to_curriculum_payload(request.curriculum, attachments)
        attachment_response = CurriculumResourceAttachmentResponse(
            curriculum_id=request.curriculum.curriculum_id,
            enriched_curriculum=enriched,
            topic_results=topic_results,
            attachments=attachments,
            warnings=warnings,
        )
        self.store.save_attachment(attachment_response)
        return attachment_response

    def get_attachment_for_curriculum(
        self,
        curriculum_id: str,
    ) -> CurriculumResourceAttachmentResponse | None:
        return self.store.load_attachment(curriculum_id)


def candidate_to_reference(candidate: ResourceCandidate) -> ResourceReferencePayload:
    resource = candidate.resource
    return ResourceReferencePayload(
        resource_id=resource.resource_id,
        title=resource.title,
        url=resource.url,
        type=resource.type,
        source_name=resource.source_name,
        source_domain=resource.source_domain,
        difficulty=resource.difficulty,
        estimated_minutes=resource.estimated_minutes,
        quality_score=resource.quality_score,
        access=resource.access,
        why_recommended=candidate.why_this,
    )


def attach_resources_to_curriculum_payload(
    curriculum: CurriculumPlan,
    attachments: list[TopicResourceAttachment],
) -> dict[str, Any]:
    by_topic_id = {attachment.topic_id: attachment for attachment in attachments}
    enriched = curriculum.model_dump(mode="json")
    for week in enriched["weeks"]:
        for topic in week["topics"]:
            attachment = by_topic_id.get(topic["topic_id"])
            topic["resources"] = (
                [resource.model_dump(mode="json") for resource in attachment.resources]
                if attachment is not None
                else []
            )
    return enriched


def _request_from_curriculum_topic(
    curriculum: CurriculumPlan,
    topic: CurriculumTopic,
    top_k: int,
    include_foundational_fallback: bool,
) -> ResourceRetrievalRequest:
    return ResourceRetrievalRequest(
        topic=topic.title,
        goal=curriculum.goal,
        difficulty=topic.difficulty,
        subtopics=[subtopic.title for subtopic in topic.subtopics],
        knowledge_map=curriculum.knowledge_map.model_dump(mode="json"),
        top_k=top_k,
        include_foundational_fallback=include_foundational_fallback,
    )


def get_canonical_resource_paths() -> list[str]:
    return [str(path) for path in canonical_resource_directories()]

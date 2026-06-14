from typing import Protocol

from app.adapter.errors import AdapterNotFoundError
from app.adapter.notifications import build_notification_payload
from app.adapter.replanner import build_replanned_curriculum
from app.adapter.schemas import (
    AdaptationCheckRequest,
    AdaptationDecision,
    AdaptationHistoryResponse,
    AdaptationLogPayload,
    AdaptationReplanRequest,
    AdaptationResult,
    CriticReviewSummary,
    ResourceRefreshSummary,
)
from app.adapter.signals import analyze_adaptation_signals
from app.critic.schemas import CriticReviewRequest
from app.critic.service import CriticService
from app.curriculum.schemas import CurriculumPlan, CurriculumTopic
from app.rag.schemas import (
    CurriculumResourceAttachmentResponse,
    ResourceRetrievalRequest,
    ResourceRetrievalResult,
    TopicResourceAttachment,
)
from app.rag.service import (
    ResourceService,
    attach_resources_to_curriculum_payload,
    candidate_to_reference,
)
from app.repositories import AdapterRepository, FakeAdapterRepository


class AdaptationStore(Protocol):
    def save(self, result: AdaptationResult) -> None:
        ...

    def load(self, adaptation_id: str) -> AdaptationResult | None:
        ...

    def history(self, curriculum_id: str) -> list[AdaptationResult]:
        ...

    def clear(self) -> None:
        ...


class RepositoryBackedAdaptationStore:
    def __init__(self, repository: AdapterRepository | None = None) -> None:
        self.repository = repository or FakeAdapterRepository()

    def save(self, result: AdaptationResult) -> None:
        self.repository.save_adaptation_result(result.model_dump(mode="json"))

    def load(self, adaptation_id: str) -> AdaptationResult | None:
        payload = self.repository.get_adaptation_result(adaptation_id)
        if payload is None:
            return None
        return AdaptationResult.model_validate(payload)

    def history(self, curriculum_id: str) -> list[AdaptationResult]:
        return [
            AdaptationResult.model_validate(payload)
            for payload in self.repository.get_history(curriculum_id)
        ]

    def clear(self) -> None:
        clear = getattr(self.repository, "clear", None)
        if callable(clear):
            clear()


class InMemoryAdaptationStore(RepositoryBackedAdaptationStore):
    """Backward-compatible fake repository store for tests and local demo routes."""

    def __init__(self) -> None:
        super().__init__(FakeAdapterRepository())


class AdapterService:
    def __init__(
        self,
        store: AdaptationStore | None = None,
        repository: AdapterRepository | None = None,
        resource_service: ResourceService | None = None,
        critic_service: CriticService | None = None,
    ) -> None:
        self.store = store or RepositoryBackedAdaptationStore(repository)
        self.resource_service = resource_service or ResourceService()
        self.critic_service = critic_service or CriticService()

    def check_adaptation(self, request: AdaptationCheckRequest) -> AdaptationDecision:
        return analyze_adaptation_signals(request)

    async def run_replan(self, request: AdaptationReplanRequest) -> AdaptationResult:
        decision = self.check_adaptation(request)
        if not decision.should_replan:
            result = _result_without_replan(request, decision)
            self.store.save(result)
            return result

        replanned_curriculum, diff = build_replanned_curriculum(
            curriculum=request.curriculum,
            progress_summary=request.progress_summary,
            decision=decision,
        )
        resource_attachment, refresh_summary = self._refresh_resources(
            curriculum=replanned_curriculum,
            decision=decision,
            existing=request.existing_resource_attachment,
            top_k=request.top_k,
        )
        critic_result = await self.critic_service.review_curriculum_with_resources(
            CriticReviewRequest(
                curriculum=replanned_curriculum,
                resource_attachment=resource_attachment,
                required_resources_per_topic=1,
            )
        )
        final_decision = decision.model_copy(update={"decision": "replanned"})
        notification = build_notification_payload(final_decision, diff)
        result = AdaptationResult(
            adaptation_id=final_decision.adaptation_id,
            user_id=final_decision.user_id,
            goal_id=final_decision.goal_id,
            curriculum_id=final_decision.curriculum_id,
            decision=final_decision,
            curriculum_before=request.curriculum,
            curriculum_after=replanned_curriculum,
            curriculum_diff=diff,
            resource_attachment=resource_attachment,
            resource_refresh_summary=refresh_summary,
            critic_review=CriticReviewSummary(
                approved=critic_result.approved,
                decision=critic_result.decision,
                score=critic_result.overall_quality_score,
                revision_instruction_count=len(critic_result.revision_instructions),
                warnings=critic_result.warnings,
            ),
            notification=notification,
            adaptation_log=AdaptationLogPayload(
                adaptation_id=final_decision.adaptation_id,
                curriculum_id=final_decision.curriculum_id,
                trigger_reason=final_decision.trigger_reason,
                decision=final_decision.decision,
                affected_weeks=[week.week_number for week in final_decision.affected_weeks],
                affected_topics=[
                    topic.topic_name for topic in final_decision.affected_topics
                ],
                critic_approved=critic_result.approved,
            ),
        )
        self.store.save(result)
        return result

    def get_adaptation(self, adaptation_id: str) -> AdaptationResult:
        result = self.store.load(adaptation_id)
        if result is None:
            raise AdapterNotFoundError(
                code="adaptation_not_found",
                message=f"Adaptation '{adaptation_id}' was not found.",
                status_code=404,
            )
        return result

    def get_history(self, curriculum_id: str) -> AdaptationHistoryResponse:
        return AdaptationHistoryResponse(
            curriculum_id=curriculum_id,
            adaptations=self.store.history(curriculum_id),
        )

    def _refresh_resources(
        self,
        curriculum: CurriculumPlan,
        decision: AdaptationDecision,
        existing: CurriculumResourceAttachmentResponse | None,
        top_k: int,
    ) -> tuple[CurriculumResourceAttachmentResponse, ResourceRefreshSummary]:
        affected_topic_ids = {topic.topic_id for topic in decision.affected_topics}
        affected_week_numbers = {week.week_number for week in decision.affected_weeks}
        existing_by_topic = {
            attachment.topic_id: attachment for attachment in existing.attachments
        } if existing else {}
        attachments: list[TopicResourceAttachment] = []
        topic_results: list[ResourceRetrievalResult] = []
        warnings: list[str] = []
        refreshed_names: list[str] = []
        cold_start = existing is None

        for week in curriculum.weeks:
            for topic in week.topics:
                should_refresh = (
                    topic.topic_id in affected_topic_ids
                    or week.week_number in affected_week_numbers
                    or cold_start
                )
                if should_refresh:
                    result = self.resource_service.retrieve_for_topic(
                        _resource_request(curriculum, topic, top_k)
                    )
                    topic_results.append(result)
                    warnings.extend(result.warnings)
                    attachments.append(
                        TopicResourceAttachment(
                            topic_id=topic.topic_id,
                            topic=topic.title,
                            resources=[
                                candidate_to_reference(candidate)
                                for candidate in result.candidates
                            ],
                            warnings=result.warnings,
                        )
                    )
                    if not cold_start:
                        refreshed_names.append(topic.title)
                    continue
                existing_attachment = existing_by_topic.get(topic.topic_id)
                if existing_attachment is not None:
                    attachments.append(existing_attachment)

        enriched = attach_resources_to_curriculum_payload(curriculum, attachments)
        if cold_start:
            warnings.append(
                "No existing resource attachment was provided; all topics were attached once."
            )
        return (
            CurriculumResourceAttachmentResponse(
                curriculum_id=curriculum.curriculum_id,
                enriched_curriculum=enriched,
                topic_results=topic_results,
                attachments=attachments,
                warnings=warnings,
            ),
            ResourceRefreshSummary(
                refreshed_week_numbers=sorted(affected_week_numbers),
                refreshed_topic_count=len(refreshed_names)
                if not cold_start
                else len([topic for week in curriculum.weeks for topic in week.topics]),
                refreshed_topic_names=refreshed_names
                if not cold_start
                else [topic.title for week in curriculum.weeks for topic in week.topics],
                used_existing_unaffected_resources=existing is not None,
                warnings=warnings,
            ),
        )


def _result_without_replan(
    request: AdaptationReplanRequest,
    decision: AdaptationDecision,
) -> AdaptationResult:
    notification = build_notification_payload(decision, None)
    return AdaptationResult(
        adaptation_id=decision.adaptation_id,
        user_id=decision.user_id,
        goal_id=decision.goal_id,
        curriculum_id=decision.curriculum_id,
        decision=decision,
        curriculum_before=request.curriculum,
        notification=notification,
        adaptation_log=AdaptationLogPayload(
            adaptation_id=decision.adaptation_id,
            curriculum_id=decision.curriculum_id,
            trigger_reason=decision.trigger_reason,
            decision=decision.decision,
            affected_weeks=[week.week_number for week in decision.affected_weeks],
            affected_topics=[topic.topic_name for topic in decision.affected_topics],
        ),
    )


def _resource_request(
    curriculum: CurriculumPlan,
    topic: CurriculumTopic,
    top_k: int,
) -> ResourceRetrievalRequest:
    return ResourceRetrievalRequest(
        topic=topic.title,
        goal=curriculum.goal,
        difficulty=topic.difficulty,
        subtopics=[subtopic.title for subtopic in topic.subtopics],
        knowledge_map=curriculum.knowledge_map.model_dump(mode="json"),
        top_k=top_k,
        include_foundational_fallback=True,
    )

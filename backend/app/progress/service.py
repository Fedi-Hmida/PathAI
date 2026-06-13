from typing import Protocol

from app.curriculum.schemas import CurriculumPlan
from app.progress.analytics import compute_progress_analytics
from app.progress.constants import ProgressEventType, TopicStatus, utc_now
from app.progress.errors import ProgressInputError, ProgressNotFoundError
from app.progress.schemas import (
    CurriculumProgressSummary,
    ProgressEvent,
    ProgressInitializeRequest,
    ProgressInitializeResponse,
    ProgressUpdateRequest,
    ProgressUpdateResponse,
    TopicProgress,
    WeekProgress,
    WeekProgressResponse,
)
from app.repositories import FakeProgressRepository, ProgressRepository


class ProgressStore(Protocol):
    def save(self, summary: CurriculumProgressSummary) -> None:
        ...

    def save(self, summary: CurriculumProgressSummary) -> None:
        ...

    def load(self, curriculum_id: str) -> CurriculumProgressSummary | None:
        ...

    def clear(self) -> None:
        ...


class RepositoryBackedProgressStore:
    def __init__(self, repository: ProgressRepository | None = None) -> None:
        self.repository = repository or FakeProgressRepository()

    def save(self, summary: CurriculumProgressSummary) -> None:
        self.repository.initialize_progress(summary.model_dump(mode="json"))

    def load(self, curriculum_id: str) -> CurriculumProgressSummary | None:
        payload = self.repository.get_progress(curriculum_id)
        if payload is None:
            return None
        return CurriculumProgressSummary.model_validate(payload)

    def clear(self) -> None:
        clear = getattr(self.repository, "clear", None)
        if callable(clear):
            clear()


class InMemoryProgressStore(RepositoryBackedProgressStore):
    """Backward-compatible fake repository store for tests and local demo routes."""

    def __init__(self) -> None:
        super().__init__(FakeProgressRepository())


class ProgressService:
    def __init__(
        self,
        store: ProgressStore | None = None,
        repository: ProgressRepository | None = None,
    ) -> None:
        self.store = store or RepositoryBackedProgressStore(repository)

    def initialize_progress(
        self,
        request: ProgressInitializeRequest,
    ) -> ProgressInitializeResponse:
        summary = _build_initial_summary(request.curriculum, request.user_id, request.goal_id)
        event = ProgressEvent(
            curriculum_id=summary.curriculum_id,
            week_number=1,
            event="initialized",
            value={"week_count": len(summary.weeks)},
        )
        summary.events.append(event)
        summary = _refresh_summary(summary)
        self.store.save(summary)
        return ProgressInitializeResponse(summary=summary)

    def update_progress(self, request: ProgressUpdateRequest) -> ProgressUpdateResponse:
        summary = self._require_summary(request.curriculum_id)
        event_type = _event_from_update(request.status, request.event)
        topic = _find_topic(summary, request.week_number, request.topic_id, request.topic_name)
        event_value = dict(request.value)
        if request.status:
            topic.status = request.status
        if event_type == "quiz_completed":
            score = _extract_score(event_value)
            topic.quiz_score = score
            _find_week(summary, request.week_number).quiz_score = score
        topic.updated_at = utc_now()
        event = ProgressEvent(
            curriculum_id=summary.curriculum_id,
            week_number=request.week_number,
            topic_id=topic.topic_id,
            topic_name=topic.topic_name,
            event=event_type,
            value=event_value,
        )
        summary.events.append(event)
        summary = _refresh_summary(summary)
        self.store.save(summary)
        return ProgressUpdateResponse(summary=summary, event=event)

    def get_summary(self, curriculum_id: str) -> CurriculumProgressSummary:
        return self._require_summary(curriculum_id)

    def get_week(self, curriculum_id: str, week_number: int) -> WeekProgressResponse:
        summary = self._require_summary(curriculum_id)
        return WeekProgressResponse(week=_find_week(summary, week_number))

    def _require_summary(self, curriculum_id: str) -> CurriculumProgressSummary:
        summary = self.store.load(curriculum_id)
        if summary is None:
            raise ProgressNotFoundError(
                code="progress_not_found",
                message=f"Progress summary '{curriculum_id}' was not found.",
                status_code=404,
            )
        return summary


def _build_initial_summary(
    curriculum: CurriculumPlan,
    user_id: str,
    goal_id: str | None,
) -> CurriculumProgressSummary:
    weeks: list[WeekProgress] = []
    for week in curriculum.weeks:
        topics = [
            TopicProgress(
                topic_id=topic.topic_id,
                topic_name=topic.title,
                week_number=week.week_number,
                estimated_hours=topic.estimated_hours,
            )
            for topic in week.topics
        ]
        weeks.append(
            WeekProgress(
                curriculum_id=curriculum.curriculum_id,
                week_number=week.week_number,
                theme=week.theme,
                topics=topics,
            )
        )
    summary = CurriculumProgressSummary(
        curriculum_id=curriculum.curriculum_id,
        user_id=user_id,
        goal_id=goal_id or curriculum.goal_id,
        goal=curriculum.goal,
        current_week_number=weeks[0].week_number if weeks else None,
        weeks=weeks,
        analytics=compute_progress_analytics(weeks),
    )
    return _refresh_summary(summary)


def _refresh_summary(summary: CurriculumProgressSummary) -> CurriculumProgressSummary:
    updated_weeks = [_refresh_week(week) for week in summary.weeks]
    current_week = next((week for week in updated_weeks if week.status != "done"), None)
    return summary.model_copy(
        update={
            "weeks": updated_weeks,
            "current_week_number": current_week.week_number if current_week else None,
            "analytics": compute_progress_analytics(updated_weeks),
            "updated_at": utc_now(),
        },
        deep=True,
    )


def _refresh_week(week: WeekProgress) -> WeekProgress:
    total = len(week.topics)
    done = sum(1 for topic in week.topics if topic.status == "done")
    stuck = any(topic.status == "stuck" for topic in week.topics)
    in_progress = any(topic.status == "in_progress" for topic in week.topics)
    completion = round((done / total) * 100, 2) if total else 0.0
    if total and done == total:
        status = "done"
    elif stuck:
        status = "stuck"
    elif done or in_progress or week.quiz_score is not None:
        status = "in_progress"
    else:
        status = "pending"
    return week.model_copy(
        update={
            "status": status,
            "completion_percentage": completion,
            "updated_at": utc_now(),
        },
        deep=True,
    )


def _event_from_update(
    status: TopicStatus | None,
    event: ProgressEventType | None,
) -> ProgressEventType:
    if event is not None:
        return event
    if status == "done":
        return "marked_done"
    if status == "stuck":
        return "marked_stuck"
    if status == "in_progress":
        return "marked_in_progress"
    raise ProgressInputError(
        code="progress_update_missing_event",
        message="Progress update requires either a status or explicit event.",
        status_code=422,
    )


def _find_week(summary: CurriculumProgressSummary, week_number: int) -> WeekProgress:
    for week in summary.weeks:
        if week.week_number == week_number:
            return week
    raise ProgressInputError(
        code="progress_week_not_found",
        message=f"Week {week_number} was not found for curriculum '{summary.curriculum_id}'.",
        status_code=404,
    )


def _find_topic(
    summary: CurriculumProgressSummary,
    week_number: int,
    topic_id: str | None,
    topic_name: str | None,
) -> TopicProgress:
    week = _find_week(summary, week_number)
    normalized_name = topic_name.lower().strip() if topic_name else None
    for topic in week.topics:
        if topic_id and topic.topic_id == topic_id:
            return topic
        if normalized_name and topic.topic_name.lower() == normalized_name:
            return topic
    raise ProgressInputError(
        code="progress_topic_not_found",
        message=f"Topic was not found in week {week_number}.",
        status_code=404,
    )


def _extract_score(value: dict[str, object]) -> float:
    raw_score = value.get("score")
    if not isinstance(raw_score, int | float):
        raise ProgressInputError(
            code="progress_quiz_score_missing",
            message="quiz_completed progress events require a numeric score value.",
            status_code=422,
        )
    score = float(raw_score)
    if score > 1:
        score = score / 100
    if score < 0 or score > 1:
        raise ProgressInputError(
            code="progress_quiz_score_invalid",
            message="Quiz score must be between 0 and 1, or between 0 and 100.",
            status_code=422,
        )
    return round(score, 3)

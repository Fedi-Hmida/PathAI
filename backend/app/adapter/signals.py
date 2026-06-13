from app.adapter.constants import (
    AHEAD_OF_SCHEDULE_WEEK_DELTA,
    BEHIND_SCHEDULE_COMPLETION_THRESHOLD,
    LOW_QUIZ_SCORE_THRESHOLD,
    REPEATED_STUCK_TOPIC_THRESHOLD,
    AdaptationSignalSeverity,
    AdaptationTriggerReason,
)
from app.adapter.schemas import (
    AdaptationCheckRequest,
    AdaptationDecision,
    AdaptationSignal,
    AffectedTopic,
    AffectedWeek,
)
from app.progress.schemas import WeekProgress


def analyze_adaptation_signals(request: AdaptationCheckRequest) -> AdaptationDecision:
    signals: list[AdaptationSignal] = []
    affected_topics: list[AffectedTopic] = []

    if request.manual_trigger:
        signals.append(
            AdaptationSignal(
                reason="manual_request",
                severity="warning",
                message=request.trigger_note or "Manual adaptation was requested.",
                value={"manual_trigger": True},
            )
        )

    current_week = _current_week(request)
    if current_week is not None:
        signals.extend(_signals_for_current_week(request, current_week))
        affected_topics.extend(_affected_stuck_topics(current_week))

    quiz_signals = _quiz_signals(request)
    signals.extend(quiz_signals)
    affected_topics.extend(_affected_low_quiz_topics(request))

    ahead_signal = _ahead_of_schedule_signal(request)
    if ahead_signal is not None:
        signals.append(ahead_signal)

    affected_topics = _dedupe_topics(affected_topics)
    affected_weeks = _affected_weeks(signals, affected_topics, current_week)
    trigger_reason = _primary_reason(signals)
    should_replan = trigger_reason in {
        "manual_request",
        "behind_schedule",
        "repeated_stuck_topics",
        "low_quiz_score",
        "ahead_of_schedule",
    }

    if not signals:
        signals.append(
            AdaptationSignal(
                reason="none",
                severity="info",
                message="No adaptation trigger was detected.",
                value={
                    "completion_percentage": (
                        request.progress_summary.analytics.completion_percentage
                    )
                },
            )
        )

    return AdaptationDecision(
        user_id=request.progress_summary.user_id,
        goal_id=request.progress_summary.goal_id,
        curriculum_id=request.curriculum.curriculum_id,
        decision="replan_recommended" if should_replan else "no_replan",
        should_replan=should_replan,
        trigger_reason=trigger_reason,
        trigger_details=_trigger_details(trigger_reason, signals),
        signals=signals,
        affected_weeks=affected_weeks,
        affected_topics=affected_topics,
        flow=["adapter", "curriculum", "resource", "critic", "persist", "notify"]
        if should_replan
        else ["adapter"],
    )


def _signals_for_current_week(
    request: AdaptationCheckRequest,
    week: WeekProgress,
) -> list[AdaptationSignal]:
    signals: list[AdaptationSignal] = []
    stuck_topics = [topic for topic in week.topics if topic.status == "stuck"]
    if len(stuck_topics) >= REPEATED_STUCK_TOPIC_THRESHOLD:
        signals.append(
            AdaptationSignal(
                reason="repeated_stuck_topics",
                severity="warning",
                message=f"Week {week.week_number} has multiple stuck topics.",
                week_number=week.week_number,
                value={"stuck_topic_count": len(stuck_topics)},
            )
        )

    if (
        request.expected_week_number is not None
        and week.week_number <= request.expected_week_number
        and week.completion_percentage < BEHIND_SCHEDULE_COMPLETION_THRESHOLD
    ):
        signals.append(
            AdaptationSignal(
                reason="behind_schedule",
                severity="warning",
                message=(
                    f"Week {week.week_number} is below the expected completion threshold."
                ),
                week_number=week.week_number,
                value={
                    "completion_percentage": week.completion_percentage,
                    "expected_week_number": request.expected_week_number,
                },
            )
        )

    if week.completion_percentage >= 100:
        signals.append(
            AdaptationSignal(
                reason="completed_week",
                severity="info",
                message=f"Week {week.week_number} is complete.",
                week_number=week.week_number,
            )
        )
    return signals


def _quiz_signals(request: AdaptationCheckRequest) -> list[AdaptationSignal]:
    if request.quiz_history is None:
        return []
    low_attempts = [
        attempt
        for attempt in request.quiz_history.attempts
        if attempt.score < LOW_QUIZ_SCORE_THRESHOLD
    ]
    if not low_attempts:
        return []
    latest = low_attempts[-1]
    severity: AdaptationSignalSeverity = (
        "critical" if len(low_attempts) >= 2 else "warning"
    )
    return [
        AdaptationSignal(
            reason="low_quiz_score",
            severity=severity,
            message="Quiz score is below the adaptation threshold.",
            week_number=latest.week_number,
            value={
                "score": latest.score,
                "low_score_count": len(low_attempts),
                "threshold": LOW_QUIZ_SCORE_THRESHOLD,
            },
        )
    ]


def _ahead_of_schedule_signal(
    request: AdaptationCheckRequest,
) -> AdaptationSignal | None:
    expected = request.expected_week_number
    if expected is None:
        return None
    completed = request.progress_summary.analytics.completed_week_count
    if completed >= expected + AHEAD_OF_SCHEDULE_WEEK_DELTA:
        return AdaptationSignal(
            reason="ahead_of_schedule",
            severity="info",
            message="Learner appears ahead of the expected weekly pace.",
            value={"completed_week_count": completed, "expected_week_number": expected},
        )
    return None


def _affected_low_quiz_topics(request: AdaptationCheckRequest) -> list[AffectedTopic]:
    if request.quiz_history is None:
        return []
    affected: list[AffectedTopic] = []
    low_weeks = {
        attempt.week_number
        for attempt in request.quiz_history.attempts
        if attempt.score < LOW_QUIZ_SCORE_THRESHOLD
    }
    for week in request.progress_summary.weeks:
        if week.week_number in low_weeks:
            affected.extend(
                AffectedTopic(
                    week_number=week.week_number,
                    topic_id=topic.topic_id,
                    topic_name=topic.topic_name,
                    reason="low_quiz_score",
                )
                for topic in week.topics
            )
    return affected


def _affected_stuck_topics(week: WeekProgress) -> list[AffectedTopic]:
    return [
        AffectedTopic(
            week_number=week.week_number,
            topic_id=topic.topic_id,
            topic_name=topic.topic_name,
            reason="repeated_stuck_topics",
        )
        for topic in week.topics
        if topic.status == "stuck"
    ]


def _current_week(request: AdaptationCheckRequest) -> WeekProgress | None:
    if request.progress_summary.current_week_number is None:
        return None
    for week in request.progress_summary.weeks:
        if week.week_number == request.progress_summary.current_week_number:
            return week
    return None


def _affected_weeks(
    signals: list[AdaptationSignal],
    affected_topics: list[AffectedTopic],
    current_week: WeekProgress | None,
) -> list[AffectedWeek]:
    by_week: dict[int, AffectedWeek] = {}
    for topic in affected_topics:
        by_week[topic.week_number] = AffectedWeek(
            week_number=topic.week_number,
            reason=topic.reason,
            topic_count=sum(1 for item in affected_topics if item.week_number == topic.week_number),
        )
    if not by_week and current_week is not None:
        for signal in signals:
            if signal.reason in {"manual_request", "behind_schedule", "ahead_of_schedule"}:
                by_week[current_week.week_number] = AffectedWeek(
                    week_number=current_week.week_number,
                    reason=signal.reason,
                    topic_count=len(current_week.topics),
                )
    return sorted(by_week.values(), key=lambda week: week.week_number)


def _primary_reason(signals: list[AdaptationSignal]) -> AdaptationTriggerReason:
    priority: list[AdaptationTriggerReason] = [
        "manual_request",
        "repeated_stuck_topics",
        "low_quiz_score",
        "behind_schedule",
        "ahead_of_schedule",
        "completed_week",
    ]
    reasons = {signal.reason for signal in signals}
    for reason in priority:
        if reason in reasons:
            return reason
    return "none"


def _trigger_details(reason: str, signals: list[AdaptationSignal]) -> str:
    if reason == "none":
        return "No adaptation trigger was detected."
    messages = [signal.message for signal in signals if signal.reason == reason]
    return " ".join(messages) if messages else f"Adaptation triggered by {reason}."


def _dedupe_topics(topics: list[AffectedTopic]) -> list[AffectedTopic]:
    seen: set[tuple[int, str]] = set()
    deduped: list[AffectedTopic] = []
    for topic in topics:
        key = (topic.week_number, topic.topic_id)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(topic)
    return deduped

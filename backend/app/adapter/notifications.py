from app.adapter.schemas import AdaptationDecision, CurriculumDiff, NotificationPayload


def build_notification_payload(
    decision: AdaptationDecision,
    diff: CurriculumDiff | None,
) -> NotificationPayload:
    affected_weeks = [week.week_number for week in decision.affected_weeks]
    if diff is None:
        change_summary = "No curriculum changes were made."
    else:
        change_summary = diff.summary
    return NotificationPayload(
        title="Your learning plan was reviewed",
        message=_message(decision, affected_weeks),
        reason=decision.trigger_reason,
        affected_weeks=affected_weeks,
        change_summary=change_summary,
    )


def _message(decision: AdaptationDecision, affected_weeks: list[int]) -> str:
    if not decision.should_replan:
        return "Your progress does not require a curriculum change right now."
    week_text = ", ".join(str(week) for week in affected_weeks) or "the current week"
    return (
        "PathAI detected a learning signal and prepared an updated plan for "
        f"week(s): {week_text}. Reason: {decision.trigger_details}"
    )

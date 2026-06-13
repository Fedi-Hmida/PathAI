from app.adapter.schemas import AdaptationDecision, CurriculumDiff
from app.curriculum.planner import build_deterministic_curriculum
from app.curriculum.schemas import (
    CurriculumGenerationRequest,
    CurriculumMilestone,
    CurriculumPlan,
    CurriculumTopic,
    CurriculumWeek,
)
from app.progress.schemas import CurriculumProgressSummary


def build_replanned_curriculum(
    curriculum: CurriculumPlan,
    progress_summary: CurriculumProgressSummary,
    decision: AdaptationDecision,
) -> tuple[CurriculumPlan, CurriculumDiff]:
    affected_week_numbers = {week.week_number for week in decision.affected_weeks}
    completed_week_numbers = {
        week.week_number for week in progress_summary.weeks if week.status == "done"
    }
    regenerated = build_deterministic_curriculum(
        CurriculumGenerationRequest(
            user_id=curriculum.user_id,
            goal_id=curriculum.goal_id,
            assessment_session_id=curriculum.assessment_session_id,
            goal=curriculum.goal,
            timeline_weeks=curriculum.timeline_weeks,
            hours_per_week=curriculum.hours_per_week,
            knowledge_map=curriculum.knowledge_map,
        )
    )
    regenerated_by_week = {week.week_number: week for week in regenerated.weeks}
    updated_weeks: list[CurriculumWeek] = []
    changed_weeks: list[int] = []
    preserved_weeks: list[int] = []
    changed_topics: list[str] = []

    for week in curriculum.weeks:
        if week.week_number in completed_week_numbers:
            updated_weeks.append(week)
            preserved_weeks.append(week.week_number)
            continue
        if week.week_number in affected_week_numbers:
            adapted = _adapt_week(
                regenerated_by_week.get(week.week_number, week),
                decision.trigger_reason,
            )
            updated_weeks.append(adapted)
            changed_weeks.append(week.week_number)
            changed_topics.extend(topic.title for topic in adapted.topics)
            continue
        updated_weeks.append(week)
        preserved_weeks.append(week.week_number)

    if not changed_weeks and decision.affected_weeks:
        first = decision.affected_weeks[0].week_number
        updated_weeks = [
            _adapt_week(week, decision.trigger_reason) if week.week_number == first else week
            for week in updated_weeks
        ]
        changed_weeks.append(first)
        changed_topics.extend(
            topic.title
            for week in updated_weeks
            if week.week_number == first
            for topic in week.topics
        )

    updated = curriculum.model_copy(
        update={
            "weeks": updated_weeks,
            "total_hours": round(sum(week.estimated_hours for week in updated_weeks), 2),
            "generation_notes": [
                *curriculum.generation_notes,
                "Adapter replanned affected weeks only; completed weeks were preserved.",
            ],
            "status": "generated",
        },
        deep=True,
    )
    diff = CurriculumDiff(
        changed_week_numbers=changed_weeks,
        preserved_week_numbers=preserved_weeks,
        changed_topic_names=changed_topics,
        summary=_diff_summary(changed_weeks, preserved_weeks, decision.trigger_reason),
    )
    return updated, diff


def _adapt_week(week: CurriculumWeek, reason: str) -> CurriculumWeek:
    adapted_topics = [_adapt_topic(topic, reason) for topic in week.topics]
    theme = _bounded(f"Adapted recovery: {week.theme}", 180)
    weekly_goal = _bounded(
        f"{week.weekly_goal} Add focused recovery work for {reason.replace('_', ' ')}.",
        500,
    )
    milestone = CurriculumMilestone(
        title=_bounded(f"Adapted {week.milestone.title}", 180),
        description=_bounded(
            f"{week.milestone.description} Adapted after progress review.",
            700,
        ),
        deliverable=week.milestone.deliverable,
        evaluation_hint=week.milestone.evaluation_hint,
    )
    return week.model_copy(
        update={
            "theme": theme,
            "weekly_goal": weekly_goal,
            "milestone": milestone,
            "topics": adapted_topics,
        },
        deep=True,
    )


def _adapt_topic(topic: CurriculumTopic, reason: str) -> CurriculumTopic:
    return topic.model_copy(
        update={
            "title": _bounded(f"Review and practice: {topic.title}", 180),
            "priority": "high",
            "rationale": _bounded(
                f"{topic.rationale} Adapted because of {reason.replace('_', ' ')}.",
                600,
            ),
            "learning_outcomes": [
                *_bounded_outcomes(topic.learning_outcomes),
                _bounded(
                    f"Recover confidence on {topic.title} through targeted practice.",
                    400,
                ),
            ][:8],
        },
        deep=True,
    )


def _bounded(value: str, limit: int) -> str:
    return value[:limit].rstrip()


def _bounded_outcomes(outcomes: list[str]) -> list[str]:
    return [_bounded(outcome, 400) for outcome in outcomes]


def _diff_summary(
    changed_weeks: list[int],
    preserved_weeks: list[int],
    reason: str,
) -> str:
    if not changed_weeks:
        return "No curriculum weeks were changed."
    changed = ", ".join(str(week) for week in changed_weeks)
    preserved = ", ".join(str(week) for week in preserved_weeks) or "none"
    return (
        f"Replanned affected week(s) {changed} because of {reason.replace('_', ' ')}. "
        f"Preserved week(s): {preserved}."
    )

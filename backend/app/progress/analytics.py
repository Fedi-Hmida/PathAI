from collections.abc import Sequence

from app.progress.constants import (
    LOW_QUIZ_SCORE_THRESHOLD,
    REPEATED_STUCK_THRESHOLD,
)
from app.progress.schemas import (
    AdapterProgressSignal,
    ProgressAnalytics,
    TopicProgress,
    WeekProgress,
)


def compute_progress_analytics(weeks: list[WeekProgress]) -> ProgressAnalytics:
    topics = [topic for week in weeks for topic in week.topics]
    total_topic_count = len(topics)
    completed_topic_count = sum(1 for topic in topics if topic.status == "done")
    stuck_topics = [topic for topic in topics if topic.status == "stuck"]
    completed_week_count = sum(1 for week in weeks if week.status == "done")
    quiz_scores = [week.quiz_score for week in weeks if week.quiz_score is not None]
    low_quiz_scores = [
        score for score in quiz_scores if score < LOW_QUIZ_SCORE_THRESHOLD
    ]
    completion_percentage = (
        round((completed_topic_count / total_topic_count) * 100, 2)
        if total_topic_count
        else 0.0
    )

    signals = _adapter_signals(
        weeks=weeks,
        completion_percentage=completion_percentage,
        stuck_topics=stuck_topics,
        low_quiz_scores=low_quiz_scores,
    )

    return ProgressAnalytics(
        completion_percentage=completion_percentage,
        completed_topic_count=completed_topic_count,
        total_topic_count=total_topic_count,
        stuck_topic_count=len(stuck_topics),
        completed_week_count=completed_week_count,
        total_week_count=len(weeks),
        average_quiz_score=round(sum(quiz_scores) / len(quiz_scores), 3)
        if quiz_scores
        else None,
        low_quiz_score_count=len(low_quiz_scores),
        signals=signals,
    )


def _adapter_signals(
    weeks: list[WeekProgress],
    completion_percentage: float,
    stuck_topics: Sequence[TopicProgress],
    low_quiz_scores: list[float],
) -> list[AdapterProgressSignal]:
    signals: list[AdapterProgressSignal] = []
    completed_weeks = [week for week in weeks if week.status == "done"]

    if completed_weeks:
        latest = completed_weeks[-1]
        signals.append(
            AdapterProgressSignal(
                signal="completed_week",
                severity="info",
                message=f"Week {latest.week_number} is complete.",
                week_number=latest.week_number,
            )
        )

    if len(stuck_topics) >= REPEATED_STUCK_THRESHOLD:
        signals.append(
            AdapterProgressSignal(
                signal="repeated_stuck_topics",
                severity="warning",
                message="Learner has multiple stuck topics.",
                value={"stuck_topic_count": len(stuck_topics)},
            )
        )

    if low_quiz_scores:
        signals.append(
            AdapterProgressSignal(
                signal="low_quiz_score",
                severity="warning",
                message="Recent quiz score is below the future adaptation threshold.",
                value={"low_quiz_score_count": len(low_quiz_scores)},
            )
        )

    first_incomplete = next((week for week in weeks if week.status != "done"), None)
    if first_incomplete and first_incomplete.week_number > 1 and completion_percentage < 50:
        signals.append(
            AdapterProgressSignal(
                signal="behind_schedule_candidate",
                severity="warning",
                message="Learner may be falling behind the planned sequence.",
                week_number=first_incomplete.week_number,
                value={"completion_percentage": completion_percentage},
            )
        )

    if not signals:
        signals.append(
            AdapterProgressSignal(
                signal="on_track",
                severity="info",
                message="No adaptation risk signals detected.",
                value={"completion_percentage": completion_percentage},
            )
        )

    return signals

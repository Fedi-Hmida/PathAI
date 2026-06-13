from app.curriculum.schemas import CurriculumPlan, CurriculumValidationIssue


def validate_curriculum_plan(plan: CurriculumPlan) -> list[CurriculumValidationIssue]:
    issues: list[CurriculumValidationIssue] = []

    if len(plan.weeks) != plan.timeline_weeks:
        issues.append(
            CurriculumValidationIssue(
                code="timeline_length_mismatch",
                message="Curriculum week count does not match requested timeline.",
                severity="error",
            )
        )

    expected_week_numbers = list(range(1, len(plan.weeks) + 1))
    actual_week_numbers = [week.week_number for week in plan.weeks]
    if actual_week_numbers != expected_week_numbers:
        issues.append(
            CurriculumValidationIssue(
                code="week_numbers_not_sequential",
                message="Curriculum weeks must be numbered sequentially starting at 1.",
                severity="error",
            )
        )

    for week in plan.weeks:
        if week.estimated_hours > plan.hours_per_week:
            issues.append(
                CurriculumValidationIssue(
                    code="weekly_hours_exceeded",
                    message="Week estimated hours exceed learner availability.",
                    severity="error",
                    week_number=week.week_number,
                )
            )
        if not week.topics:
            issues.append(
                CurriculumValidationIssue(
                    code="week_has_no_topics",
                    message="Every week must include at least one topic.",
                    severity="error",
                    week_number=week.week_number,
                )
            )

    if plan.weeks and not plan.weeks[-1].project_or_application:
        issues.append(
            CurriculumValidationIssue(
                code="missing_final_project_week",
                message="The final week should be project or application focused.",
                severity="error",
                week_number=plan.weeks[-1].week_number,
            )
        )

    max_total_hours = plan.timeline_weeks * plan.hours_per_week
    if plan.total_hours > max_total_hours:
        issues.append(
            CurriculumValidationIssue(
                code="total_hours_exceeded",
                message="Curriculum total hours exceed requested time budget.",
                severity="error",
            )
        )

    if len(plan.difficulty_progression.weekly_levels) != len(plan.weeks):
        issues.append(
            CurriculumValidationIssue(
                code="difficulty_progression_mismatch",
                message="Difficulty progression must include one level per week.",
                severity="error",
            )
        )

    return issues

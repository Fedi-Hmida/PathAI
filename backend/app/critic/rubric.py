from urllib.parse import urlparse

from app.critic.constants import (
    APPROVAL_THRESHOLD,
    DEFAULT_MAX_REVISIONS,
    CriticDecisionStatus,
)
from app.critic.schemas import (
    CriticReviewRequest,
    CriticReviewResult,
    CriticRubricSummary,
    CurriculumIssue,
    DifficultyReview,
    PacingReview,
    PrerequisiteReview,
    QualityScoreBreakdown,
    ResourceCoverageReview,
    ResourceIssue,
    RevisionInstruction,
)
from app.curriculum.constants import DifficultyLevel
from app.curriculum.schemas import CurriculumPlan, CurriculumTopic
from app.rag.schemas import ResourceReferencePayload

CriticIssue = CurriculumIssue | ResourceIssue

DIFFICULTY_ORDER: dict[DifficultyLevel, int] = {
    "beginner": 0,
    "intermediate": 1,
    "advanced": 2,
}


def get_rubric_summary() -> CriticRubricSummary:
    return CriticRubricSummary(
        approval_threshold=APPROVAL_THRESHOLD,
        required_resources_per_topic=2,
        max_revisions=DEFAULT_MAX_REVISIONS,
        curriculum_checks=[
            "Week count must match timeline_weeks.",
            "Week numbers must be sequential.",
            "Weekly estimated hours must not exceed hours_per_week.",
            "Final week or final two weeks should include project/application work.",
            "Weak and missing knowledge-map topics should be addressed.",
            "Strong topics should not dominate the curriculum unless used as prerequisites.",
            "Difficulty progression should be coherent and non-regressive.",
            "Each topic should include learning outcomes.",
            "Each week should include a milestone.",
        ],
        resource_checks=[
            "Each topic should have at least the required number of resources.",
            "Resource difficulty should match or be close to topic difficulty.",
            "Resource URLs must be HTTP(S).",
            "Resource types and sources should not be overly repetitive.",
            "why_this explanations should be specific and actionable.",
            "Foundational resources should not be overused for advanced topics.",
        ],
        decision_rules=[
            "Approve when score is above threshold and no critical issues exist.",
            "Reject when critical issues exist or score falls below threshold.",
            "If max revisions are reached, force approval with auto_approved metadata.",
        ],
    )


def review_with_deterministic_rubric(request: CriticReviewRequest) -> CriticReviewResult:
    curriculum = request.curriculum
    curriculum_issues = _curriculum_issues(curriculum)
    resource_issues = _resource_issues(request)
    warnings = _warnings(request)

    pacing_review = _pacing_review(curriculum, curriculum_issues)
    prerequisite_review = _prerequisite_review(curriculum, curriculum_issues)
    difficulty_review = _difficulty_review(curriculum, curriculum_issues)
    coverage_review = _coverage_review(request, resource_issues)

    pacing_score = pacing_review.score
    prerequisite_score = prerequisite_review.score
    difficulty_score = difficulty_review.score
    coverage_score = coverage_review.score
    resource_score = _score_from_issues(resource_issues)
    curriculum_score = _score_from_issues(curriculum_issues)
    overall_score = _weighted_overall(
        curriculum_score=curriculum_score,
        resource_score=resource_score,
        pacing_score=pacing_score,
        prerequisite_score=prerequisite_score,
        difficulty_score=difficulty_score,
        coverage_score=coverage_score,
    )
    critical_issue_count = sum(
        1 for issue in curriculum_issues if issue.severity == "critical"
    )
    critical_issue_count += sum(
        1 for issue in resource_issues if issue.severity == "critical"
    )
    approved = overall_score >= APPROVAL_THRESHOLD and critical_issue_count == 0
    auto_approved = False
    decision: CriticDecisionStatus = "approved" if approved else "rejected"

    if not approved and request.revision_count >= request.max_revisions:
        approved = True
        auto_approved = True
        decision = "auto_approved"
        warnings.append("Auto-approved after max revision count; manual review required.")

    return CriticReviewResult(
        curriculum_id=curriculum.curriculum_id,
        goal=curriculum.goal,
        timeline_weeks=curriculum.timeline_weeks,
        hours_per_week=curriculum.hours_per_week,
        approved=approved,
        decision=decision,
        overall_quality_score=overall_score,
        scores=QualityScoreBreakdown(
            curriculum_score=curriculum_score,
            resource_score=resource_score,
            pacing_score=pacing_score,
            prerequisite_score=prerequisite_score,
            difficulty_score=difficulty_score,
            coverage_score=coverage_score,
        ),
        pacing_review=pacing_review,
        prerequisite_review=prerequisite_review,
        difficulty_review=difficulty_review,
        resource_coverage_review=coverage_review,
        curriculum_issues=curriculum_issues,
        resource_issues=resource_issues,
        warnings=warnings,
        revision_instructions=_revision_instructions(curriculum_issues, resource_issues),
        auto_approved=auto_approved,
        metadata={
            "revision_count": request.revision_count,
            "max_revisions": request.max_revisions,
            "critical_issue_count": critical_issue_count,
        },
    )


def _curriculum_issues(curriculum: CurriculumPlan) -> list[CurriculumIssue]:
    issues: list[CurriculumIssue] = []
    if len(curriculum.weeks) != curriculum.timeline_weeks:
        issues.append(
            CurriculumIssue(
                code="week_count_mismatch",
                message="Curriculum week count does not match timeline_weeks.",
                severity="critical",
                category="structure",
            )
        )

    week_numbers = [week.week_number for week in curriculum.weeks]
    expected = list(range(1, len(curriculum.weeks) + 1))
    if week_numbers != expected:
        issues.append(
            CurriculumIssue(
                code="week_order_invalid",
                message="Curriculum week numbers are not sequential.",
                severity="critical",
                category="structure",
            )
        )

    for week in curriculum.weeks:
        if week.estimated_hours > curriculum.hours_per_week:
            issues.append(
                CurriculumIssue(
                    code="weekly_hours_exceeded",
                    message=(
                        f"Week {week.week_number} exceeds the learner's "
                        "hours_per_week constraint."
                    ),
                    severity="critical",
                    category="pacing",
                    week_number=week.week_number,
                )
            )
        for topic in week.topics:
            if not topic.learning_outcomes:
                issues.append(
                    CurriculumIssue(
                        code="missing_learning_outcomes",
                        message=f"Topic '{topic.title}' has no learning outcomes.",
                        severity="critical",
                        category="structure",
                        week_number=week.week_number,
                        topic_id=topic.topic_id,
                    )
                )

    if curriculum.weeks and not curriculum.weeks[-1].project_or_application:
        issues.append(
            CurriculumIssue(
                code="missing_project_final_week",
                message="Final week is not marked as a project/application week.",
                severity="critical",
                category="pacing",
                week_number=curriculum.weeks[-1].week_number,
            )
        )

    missing_focus = _missing_focus_topics(curriculum)
    if missing_focus:
        issues.append(
            CurriculumIssue(
                code="knowledge_gaps_not_addressed",
                message=f"Knowledge-map topics not clearly addressed: {', '.join(missing_focus)}.",
                severity="critical",
                category="personalization",
            )
        )

    over_taught = _over_taught_strong_topics(curriculum)
    if over_taught:
        issues.append(
            CurriculumIssue(
                code="strong_topics_over_taught",
                message=f"Strong topics appear as primary topics: {', '.join(over_taught)}.",
                severity="warning",
                category="personalization",
            )
        )

    if not _difficulty_progression_is_coherent(curriculum):
        issues.append(
            CurriculumIssue(
                code="difficulty_regression",
                message="Difficulty progression regresses across weeks.",
                severity="warning",
                category="difficulty",
            )
        )

    return issues


def _resource_issues(request: CriticReviewRequest) -> list[ResourceIssue]:
    if not _has_resource_context(request):
        return []

    by_topic_id = _resources_by_topic_id(request)
    by_topic_name = _resources_by_topic_name(request)
    issues: list[ResourceIssue] = []
    for week in request.curriculum.weeks:
        for topic in week.topics:
            resources = by_topic_id.get(topic.topic_id) or by_topic_name.get(_key(topic.title), [])
            issues.extend(
                _issues_for_topic_resources(
                    topic=topic,
                    resources=resources,
                    required=request.required_resources_per_topic,
                )
            )
    return issues


def _issues_for_topic_resources(
    topic: CurriculumTopic,
    resources: list[ResourceReferencePayload],
    required: int,
) -> list[ResourceIssue]:
    issues: list[ResourceIssue] = []
    if len(resources) < required:
        issues.append(
            ResourceIssue(
                code="resource_coverage_gap",
                message=(
                    f"Topic '{topic.title}' has {len(resources)} resource(s); "
                    f"{required} required."
                ),
                severity="critical",
                category="coverage",
                topic_id=topic.topic_id,
            )
        )
    if len({resource.type for resource in resources}) < 2 and len(resources) >= 2:
        issues.append(
            ResourceIssue(
                code="resource_type_diversity_low",
                message=f"Topic '{topic.title}' resources use only one resource type.",
                severity="warning",
                category="resource_quality",
                topic_id=topic.topic_id,
            )
        )
    unique_sources = {resource.source_domain or resource.source_name for resource in resources}
    if len(unique_sources) < 2 and len(resources) >= 2:
        issues.append(
            ResourceIssue(
                code="resource_source_diversity_low",
                message=f"Topic '{topic.title}' resources come from only one source.",
                severity="warning",
                category="resource_quality",
                topic_id=topic.topic_id,
            )
        )

    for resource in resources:
        if not _is_http_url(resource.url):
            issues.append(
                ResourceIssue(
                    code="resource_url_invalid",
                    message=f"Resource '{resource.title}' does not use an HTTP(S) URL.",
                    severity="critical",
                    category="resource_quality",
                    topic_id=topic.topic_id,
                    resource_id=resource.resource_id,
                )
            )
        if _difficulty_distance(topic.difficulty, resource.difficulty) > 1:
            issues.append(
                ResourceIssue(
                    code="resource_difficulty_mismatch",
                    message=(
                        f"Resource '{resource.title}' is {resource.difficulty}, "
                        f"but topic '{topic.title}' is {topic.difficulty}."
                    ),
                    severity="warning",
                    category="difficulty",
                    topic_id=topic.topic_id,
                    resource_id=resource.resource_id,
                )
            )
        if not _why_this_is_specific(resource.why_recommended, topic.title):
            issues.append(
                ResourceIssue(
                    code="why_this_too_generic",
                    message=f"Resource '{resource.title}' has a weak why_this explanation.",
                    severity="warning",
                    category="explanation",
                    topic_id=topic.topic_id,
                    resource_id=resource.resource_id,
                )
            )
    return issues


def _pacing_review(
    curriculum: CurriculumPlan,
    issues: list[CurriculumIssue],
) -> PacingReview:
    relevant = [issue for issue in issues if issue.category in {"pacing", "structure"}]
    within_hours = all(
        week.estimated_hours <= curriculum.hours_per_week for week in curriculum.weeks
    )
    expected_total = curriculum.timeline_weeks * curriculum.hours_per_week
    total_plausible = curriculum.total_hours <= expected_total + 0.01
    return PacingReview(
        score=_score_from_issues(relevant),
        within_weekly_hours=within_hours,
        total_hours_plausible=total_plausible,
        notes=["Weekly hours and final project pacing were checked."],
    )


def _prerequisite_review(
    curriculum: CurriculumPlan,
    issues: list[CurriculumIssue],
) -> PrerequisiteReview:
    relevant = [
        issue
        for issue in issues
        if issue.category in {"prerequisite", "personalization", "structure"}
    ]
    return PrerequisiteReview(
        score=_score_from_issues(relevant),
        ordered_weeks=[week.week_number for week in curriculum.weeks]
        == list(range(1, len(curriculum.weeks) + 1)),
        weak_missing_topics_addressed=not _missing_focus_topics(curriculum),
        notes=["Knowledge-map coverage and week order were checked."],
    )


def _difficulty_review(
    curriculum: CurriculumPlan,
    issues: list[CurriculumIssue],
) -> DifficultyReview:
    relevant = [issue for issue in issues if issue.category == "difficulty"]
    return DifficultyReview(
        score=_score_from_issues(relevant),
        coherent_progression=_difficulty_progression_is_coherent(curriculum),
        notes=["Weekly difficulty should be non-regressive."],
    )


def _coverage_review(
    request: CriticReviewRequest,
    issues: list[ResourceIssue],
) -> ResourceCoverageReview:
    resources_by_topic = _resources_by_topic_id(request)
    topic_count = sum(len(week.topics) for week in request.curriculum.weeks)
    total_resources = sum(len(resources) for resources in resources_by_topic.values())
    average = total_resources / topic_count if topic_count else 0.0
    return ResourceCoverageReview(
        score=_score_from_issues(issues) if _has_resource_context(request) else 1.0,
        resources_reviewed=_has_resource_context(request),
        required_resources_per_topic=request.required_resources_per_topic,
        average_resources_per_topic=round(average, 2),
        notes=["Resource coverage and explanation quality were checked."]
        if _has_resource_context(request)
        else ["Resource attachment was not provided; curriculum-only review was run."],
    )


def _warnings(request: CriticReviewRequest) -> list[str]:
    if _has_resource_context(request):
        return []
    return ["Resource attachment was not provided; resource quality checks were skipped."]


def _revision_instructions(
    curriculum_issues: list[CurriculumIssue],
    resource_issues: list[ResourceIssue],
) -> list[RevisionInstruction]:
    instructions: list[RevisionInstruction] = []
    for curriculum_issue in curriculum_issues:
        _append_revision_instruction(instructions, curriculum_issue)
    for resource_issue in resource_issues:
        _append_revision_instruction(instructions, resource_issue)
    return instructions[:12]


def _append_revision_instruction(
    instructions: list[RevisionInstruction],
    issue: CriticIssue,
) -> None:
    if issue.severity == "info":
        return
    if issue.topic_id:
        target = issue.topic_id
    elif isinstance(issue, CurriculumIssue) and issue.week_number:
        target = f"week {issue.week_number}"
    else:
        target = "curriculum"
    instructions.append(
        RevisionInstruction(
            category=issue.category,
            target=target,
            instruction=_instruction_for_issue(issue.code, issue.message),
            severity=issue.severity,
        )
    )


def _instruction_for_issue(code: str, message: str) -> str:
    if code == "resource_coverage_gap":
        return f"Attach additional curated resources. Detail: {message}"
    if code == "weekly_hours_exceeded":
        return f"Reduce scope or split topics so weekly workload fits. Detail: {message}"
    if code == "missing_project_final_week":
        return "Revise the final week into a concrete project or application milestone."
    if code == "knowledge_gaps_not_addressed":
        return f"Add or reprioritize weeks for the missing/weak topics. Detail: {message}"
    if code == "why_this_too_generic":
        return (
            "Replace generic resource explanations with topic-specific rationale. "
            f"Detail: {message}"
        )
    return f"Revise this issue before delivery. Detail: {message}"


def _weighted_overall(
    curriculum_score: float,
    resource_score: float,
    pacing_score: float,
    prerequisite_score: float,
    difficulty_score: float,
    coverage_score: float,
) -> float:
    score = (
        curriculum_score * 0.24
        + resource_score * 0.24
        + pacing_score * 0.16
        + prerequisite_score * 0.14
        + difficulty_score * 0.10
        + coverage_score * 0.12
    )
    return round(max(0.0, min(score, 1.0)), 4)


def _score_from_issues(issues: list[CurriculumIssue] | list[ResourceIssue]) -> float:
    score = 1.0
    for issue in issues:
        if issue.severity == "critical":
            score -= 0.35
        elif issue.severity == "warning":
            score -= 0.12
        else:
            score -= 0.03
    return round(max(score, 0.0), 4)


def _missing_focus_topics(curriculum: CurriculumPlan) -> list[str]:
    focus = [*curriculum.knowledge_map.missing, *curriculum.knowledge_map.weak]
    searchable = " ".join(
        [
            *[week.theme for week in curriculum.weeks],
            *[topic.title for week in curriculum.weeks for topic in week.topics],
            *[
                subtopic.title
                for week in curriculum.weeks
                for topic in week.topics
                for subtopic in topic.subtopics
            ],
        ]
    ).lower()
    return [topic for topic in focus if topic.lower() not in searchable]


def _over_taught_strong_topics(curriculum: CurriculumPlan) -> list[str]:
    strong = {topic.lower() for topic in curriculum.knowledge_map.strong}
    if not strong:
        return []
    primary_topics = {
        topic.title.lower()
        for week in curriculum.weeks
        for topic in week.topics
        if not topic.project_or_application
    }
    return sorted(strong & primary_topics)


def _difficulty_progression_is_coherent(curriculum: CurriculumPlan) -> bool:
    levels = [DIFFICULTY_ORDER[week.difficulty] for week in curriculum.weeks]
    return all(
        next_level >= current for current, next_level in zip(levels, levels[1:], strict=False)
    )


def _difficulty_distance(left: DifficultyLevel, right: DifficultyLevel) -> int:
    return abs(DIFFICULTY_ORDER[left] - DIFFICULTY_ORDER[right])


def _has_resource_context(request: CriticReviewRequest) -> bool:
    return request.resource_attachment is not None or bool(request.resource_results)


def _resources_by_topic_id(
    request: CriticReviewRequest,
) -> dict[str, list[ResourceReferencePayload]]:
    if request.resource_attachment is None:
        return {}
    return {
        attachment.topic_id: attachment.resources
        for attachment in request.resource_attachment.attachments
    }


def _resources_by_topic_name(
    request: CriticReviewRequest,
) -> dict[str, list[ResourceReferencePayload]]:
    if request.resource_attachment is not None:
        return {
            _key(attachment.topic): attachment.resources
            for attachment in request.resource_attachment.attachments
        }
    return {
        _key(result.request.topic): [
            ResourceReferencePayload(
                resource_id=candidate.resource.resource_id,
                title=candidate.resource.title,
                url=candidate.resource.url,
                type=candidate.resource.type,
                source_name=candidate.resource.source_name,
                source_domain=candidate.resource.source_domain,
                difficulty=candidate.resource.difficulty,
                estimated_minutes=candidate.resource.estimated_minutes,
                quality_score=candidate.resource.quality_score,
                access=candidate.resource.access,
                why_recommended=candidate.why_this,
            )
            for candidate in result.candidates
        ]
        for result in request.resource_results
    }


def _is_http_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _why_this_is_specific(why_this: str, topic: str) -> bool:
    normalized = why_this.lower()
    topic_tokens = {token for token in _key(topic).split() if len(token) > 3}
    return len(why_this.strip()) >= 35 and bool(topic_tokens & set(normalized.split()))


def _key(value: str) -> str:
    return " ".join("".join(char.lower() if char.isalnum() else " " for char in value).split())

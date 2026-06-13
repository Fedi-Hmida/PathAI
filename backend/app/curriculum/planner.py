from app.assessment.schemas import KnowledgeMap
from app.curriculum.constants import DifficultyLevel, TopicPriority, new_uuid, utc_now
from app.curriculum.schemas import (
    CurriculumGenerationRequest,
    CurriculumMilestone,
    CurriculumPlan,
    CurriculumSubtopic,
    CurriculumTopic,
    CurriculumWeek,
    DifficultyProgression,
)


def build_deterministic_curriculum(request: CurriculumGenerationRequest) -> CurriculumPlan:
    goal = _required_goal(request)
    timeline_weeks = _required_timeline(request)
    hours_per_week = _required_hours(request)
    knowledge_map = _required_knowledge_map(request)
    now = utc_now()
    focus_topics = _build_focus_topics(knowledge_map)
    weekly_levels = _weekly_levels(knowledge_map.recommended_level, timeline_weeks)
    project_weeks = 2 if timeline_weeks >= 6 else 1
    project_start = max(1, timeline_weeks - project_weeks + 1)

    weeks: list[CurriculumWeek] = []
    for week_number in range(1, timeline_weeks + 1):
        is_project_week = week_number >= project_start
        week_topics = _topics_for_week(
            week_number=week_number,
            focus_topics=focus_topics,
            knowledge_map=knowledge_map,
            difficulty=weekly_levels[week_number - 1],
            hours_per_week=hours_per_week,
            is_project_week=is_project_week,
            goal=goal,
        )
        theme = _project_theme(goal, week_number) if is_project_week else week_topics[0].title
        weeks.append(
            CurriculumWeek(
                week_number=week_number,
                theme=theme,
                weekly_goal=_weekly_goal(theme, is_project_week),
                milestone=_milestone(theme, week_number, is_project_week),
                estimated_hours=min(
                    float(hours_per_week),
                    sum(t.estimated_hours for t in week_topics),
                ),
                difficulty=weekly_levels[week_number - 1],
                topics=week_topics,
                project_or_application=is_project_week,
            )
        )

    total_hours = round(sum(week.estimated_hours for week in weeks), 2)
    return CurriculumPlan(
        curriculum_id=new_uuid(),
        user_id=request.user_id,
        goal_id=request.goal_id,
        assessment_session_id=request.assessment_session_id,
        goal=goal,
        timeline_weeks=timeline_weeks,
        hours_per_week=hours_per_week,
        knowledge_map=knowledge_map,
        weeks=weeks,
        total_hours=total_hours,
        difficulty_progression=DifficultyProgression(
            starting_level=weekly_levels[0],
            ending_level=weekly_levels[-1],
            weekly_levels=weekly_levels,
            rationale=(
                "Difficulty starts from the assessed level and increases only after "
                "foundational weak or missing areas are scheduled."
            ),
        ),
        generation_notes=[
            "Strong topics are skipped unless needed as prerequisites.",
            "Weak and missing topics receive the highest scheduling priority.",
            "Final week is application focused; resources and Critic review come later.",
        ],
        source="deterministic",
        created_at=now,
        updated_at=now,
    )


def _build_focus_topics(knowledge_map: KnowledgeMap) -> list[tuple[TopicPriority, str]]:
    focus: list[tuple[TopicPriority, str]] = []
    focus.extend(("high", topic) for topic in knowledge_map.missing)
    focus.extend(("medium", topic) for topic in knowledge_map.weak)
    if not focus:
        focus.extend(("low", f"Deepen {topic}") for topic in knowledge_map.strong)
    if not focus:
        focus.append(("high", "Core foundations"))
    return focus


def _topics_for_week(
    week_number: int,
    focus_topics: list[tuple[TopicPriority, str]],
    knowledge_map: KnowledgeMap,
    difficulty: DifficultyLevel,
    hours_per_week: int,
    is_project_week: bool,
    goal: str,
) -> list[CurriculumTopic]:
    if is_project_week:
        topic_title = f"Apply learning to: {goal[:90]}"
        priority: TopicPriority = "high"
        base_topic = topic_title
    else:
        priority, base_topic = focus_topics[(week_number - 1) % len(focus_topics)]

    estimated_hours = max(1.0, min(float(hours_per_week), float(hours_per_week) * 0.85))
    subtopic_hours = round(estimated_hours / 3, 2)
    prerequisites = knowledge_map.strong[:2] if priority != "low" else []
    return [
        CurriculumTopic(
            topic_id=f"week-{week_number}-{_slug(base_topic)}",
            title=base_topic,
            priority=priority,
            difficulty=difficulty,
            estimated_hours=estimated_hours,
            rationale=_rationale(priority, base_topic),
            subtopics=[
                CurriculumSubtopic(
                    title=f"{base_topic} concepts",
                    estimated_hours=subtopic_hours,
                    learning_outcome=f"Explain the main ideas behind {base_topic}.",
                ),
                CurriculumSubtopic(
                    title=f"{base_topic} practice",
                    estimated_hours=subtopic_hours,
                    learning_outcome=f"Apply {base_topic} to a guided exercise.",
                ),
                CurriculumSubtopic(
                    title=f"{base_topic} reflection",
                    estimated_hours=subtopic_hours,
                    learning_outcome=f"Identify remaining gaps around {base_topic}.",
                ),
            ],
            prerequisites=prerequisites,
            learning_outcomes=[
                f"Demonstrate practical understanding of {base_topic}.",
                f"Connect {base_topic} to the stated learning goal.",
            ],
            project_or_application=is_project_week,
        )
    ]


def _weekly_levels(starting_level: DifficultyLevel, timeline_weeks: int) -> list[DifficultyLevel]:
    levels: list[DifficultyLevel] = ["beginner", "intermediate", "advanced"]
    start_index = levels.index(starting_level)
    weekly: list[DifficultyLevel] = []
    for index in range(timeline_weeks):
        if timeline_weeks <= 2:
            level_index = start_index
        else:
            level_index = min(start_index + (index * 2 // max(timeline_weeks - 1, 1)), 2)
        weekly.append(levels[level_index])
    return weekly


def _weekly_goal(theme: str, is_project_week: bool) -> str:
    if is_project_week:
        return f"Turn previous learning into a concrete application around {theme}."
    return f"Build reliable understanding and practice around {theme}."


def _milestone(theme: str, week_number: int, is_project_week: bool) -> CurriculumMilestone:
    if is_project_week:
        return CurriculumMilestone(
            title=f"Week {week_number} application milestone",
            description=f"Produce a small applied artifact demonstrating {theme}.",
            deliverable="Project note, mini-demo, or implementation checklist.",
            evaluation_hint="The learner can explain design choices and remaining gaps.",
        )
    return CurriculumMilestone(
        title=f"Week {week_number} learning milestone",
        description=f"Complete focused study and practice for {theme}.",
        deliverable="Summary notes and at least one practice exercise.",
        evaluation_hint="The learner can answer concept and application questions.",
    )


def _project_theme(goal: str, week_number: int) -> str:
    return f"Project/application week {week_number}: {goal[:80]}"


def _rationale(priority: TopicPriority, topic: str) -> str:
    if priority == "high":
        return f"Scheduled early because {topic} was identified as missing knowledge."
    if priority == "medium":
        return f"Allocated practice time because {topic} was identified as weak."
    return f"Used as a deepening topic because core gaps were limited: {topic}."


def _slug(value: str) -> str:
    return "-".join("".join(ch.lower() if ch.isalnum() else " " for ch in value).split())[:80]


def _required_goal(request: CurriculumGenerationRequest) -> str:
    if request.goal is None:
        raise ValueError("Curriculum request is missing goal.")
    return request.goal


def _required_timeline(request: CurriculumGenerationRequest) -> int:
    if request.timeline_weeks is None:
        raise ValueError("Curriculum request is missing timeline_weeks.")
    return request.timeline_weeks


def _required_hours(request: CurriculumGenerationRequest) -> int:
    if request.hours_per_week is None:
        raise ValueError("Curriculum request is missing hours_per_week.")
    return request.hours_per_week


def _required_knowledge_map(request: CurriculumGenerationRequest) -> KnowledgeMap:
    if request.knowledge_map is None:
        raise ValueError("Curriculum request is missing knowledge_map.")
    return request.knowledge_map

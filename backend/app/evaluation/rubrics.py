from app.evaluation.schemas import ReviewRubric, RubricCriterion


def get_review_rubrics() -> list[ReviewRubric]:
    return [
        ReviewRubric(
            rubric_id="curriculum_expert_review_v1",
            title="Curriculum Expert Review Rubric",
            audience="curriculum_expert",
            criteria=[
                RubricCriterion(
                    criterion="Goal alignment",
                    scale_description=(
                        "1 means weak alignment; 5 means all weeks directly support the goal."
                    ),
                    high_score_anchor=(
                        "Topics, projects, and milestones all support the learner goal."
                    ),
                    low_score_anchor="Weeks are generic or unrelated to the stated goal.",
                ),
                RubricCriterion(
                    criterion="Pacing and workload",
                    scale_description=(
                        "1 means unrealistic load; 5 means weekly effort fits the constraint."
                    ),
                    high_score_anchor="Estimated hours fit the declared hours per week.",
                    low_score_anchor="Weeks are overloaded or too shallow for the target timeline.",
                ),
                RubricCriterion(
                    criterion="Prerequisite coherence",
                    scale_description="1 means disorder; 5 means topics build naturally.",
                    high_score_anchor="Foundations appear before advanced application work.",
                    low_score_anchor="Advanced topics appear before required foundations.",
                ),
            ],
        ),
        ReviewRubric(
            rubric_id="resource_quality_review_v1",
            title="Resource Quality Review Rubric",
            audience="resource_reviewer",
            criteria=[
                RubricCriterion(
                    criterion="Topic relevance",
                    scale_description=(
                        "1 means irrelevant; 5 means resource directly supports the topic."
                    ),
                    high_score_anchor="Resource clearly teaches the target topic and subtopics.",
                    low_score_anchor="Resource has only superficial keyword overlap.",
                ),
                RubricCriterion(
                    criterion="Difficulty fit",
                    scale_description=(
                        "1 means wrong level; 5 means matches learner and week difficulty."
                    ),
                    high_score_anchor="Resource difficulty matches the curriculum stage.",
                    low_score_anchor="Resource is too advanced or too basic for the learner state.",
                ),
                RubricCriterion(
                    criterion="Access and quality",
                    scale_description=(
                        "1 means inaccessible or low quality; 5 means accessible and credible."
                    ),
                    high_score_anchor="Resource is open, current, credible, and clear.",
                    low_score_anchor="Resource is unavailable, outdated, or low credibility.",
                ),
            ],
        ),
        ReviewRubric(
            rubric_id="assessment_quality_review_v1",
            title="Assessment Quality Review Rubric",
            audience="assessment_reviewer",
            criteria=[
                RubricCriterion(
                    criterion="Diagnostic coverage",
                    scale_description=(
                        "1 means misses key topics; 5 means probes required prerequisites."
                    ),
                    high_score_anchor="Questions reveal strong, weak, and missing concepts.",
                    low_score_anchor="Questions are too generic to diagnose readiness.",
                ),
                RubricCriterion(
                    criterion="Evidence quality",
                    scale_description=(
                        "1 means unsupported labels; 5 means labels follow answer evidence."
                    ),
                    high_score_anchor="Knowledge map claims are supported by answer evidence.",
                    low_score_anchor="Knowledge map labels are arbitrary or unexplained.",
                ),
            ],
        ),
        ReviewRubric(
            rubric_id="adaptation_usefulness_review_v1",
            title="Adaptation Usefulness Review Rubric",
            audience="adaptation_reviewer",
            criteria=[
                RubricCriterion(
                    criterion="Trigger correctness",
                    scale_description=(
                        "1 means noisy triggers; 5 means adaptation only fires when useful."
                    ),
                    high_score_anchor=(
                        "Signals correctly detect stuck, behind, low-score, or ahead learners."
                    ),
                    low_score_anchor="Signals trigger replans without meaningful evidence.",
                ),
                RubricCriterion(
                    criterion="Change specificity",
                    scale_description=(
                        "1 means broad rewrite; 5 means targeted affected-week changes."
                    ),
                    high_score_anchor="Only affected weeks/topics are adjusted and explained.",
                    low_score_anchor="Replan rewrites unrelated completed work.",
                ),
            ],
        ),
    ]

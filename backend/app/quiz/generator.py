from itertools import cycle

from app.curriculum.schemas import CurriculumPlan, CurriculumTopic, CurriculumWeek
from app.quiz.constants import QuizQuestionType
from app.quiz.errors import QuizInputError
from app.quiz.schemas import Quiz, QuizGenerationRequest, QuizOption, QuizQuestion


def generate_deterministic_quiz(request: QuizGenerationRequest) -> Quiz:
    week = _find_week(request.curriculum, request.week_number)
    topic_cycle = cycle(week.topics)
    questions = [
        _build_question(index=index, week=week, topic=next(topic_cycle))
        for index in range(request.question_count)
    ]
    return Quiz(
        curriculum_id=request.curriculum.curriculum_id,
        goal_id=request.curriculum.goal_id,
        user_id=request.curriculum.user_id,
        week_number=week.week_number,
        topic_names=[topic.title for topic in week.topics],
        questions=questions,
    )


def _find_week(curriculum: CurriculumPlan, week_number: int) -> CurriculumWeek:
    for week in curriculum.weeks:
        if week.week_number == week_number:
            return week
    raise QuizInputError(
        code="quiz_week_not_found",
        message=f"Week {week_number} was not found in curriculum '{curriculum.curriculum_id}'.",
        status_code=404,
    )


def _build_question(
    index: int,
    week: CurriculumWeek,
    topic: CurriculumTopic,
) -> QuizQuestion:
    question_type: QuizQuestionType
    if index % 3 == 0:
        question_type = "multiple_choice"
    elif index % 3 == 1:
        question_type = "true_false"
    else:
        question_type = "short_answer"

    if question_type == "multiple_choice":
        return QuizQuestion(
            type=question_type,
            prompt=(
                f"Which outcome best matches the topic '{topic.title}' "
                f"in week {week.week_number}?"
            ),
            options=[
                QuizOption(option_id="A", text=topic.learning_outcomes[0]),
                QuizOption(option_id="B", text=f"Ignore {topic.title} until the final week."),
                QuizOption(option_id="C", text="Study only unrelated theory."),
                QuizOption(option_id="D", text="Skip practice and resources."),
            ],
            correct_answer="A",
            explanation=f"'{topic.title}' is included to support: {topic.learning_outcomes[0]}",
            difficulty=topic.difficulty,
            topic_id=topic.topic_id,
            topic_name=topic.title,
        )

    if question_type == "true_false":
        return QuizQuestion(
            type=question_type,
            prompt=f"True or false: '{topic.title}' supports the week theme '{week.theme}'.",
            options=[
                QuizOption(option_id="true", text="True"),
                QuizOption(option_id="false", text="False"),
            ],
            correct_answer="true",
            explanation=f"The topic is part of week {week.week_number}: {week.weekly_goal}",
            difficulty=topic.difficulty,
            topic_id=topic.topic_id,
            topic_name=topic.title,
        )

    return QuizQuestion(
        type=question_type,
        prompt=(
            "In one short phrase, name the main topic connected to this outcome: "
            f"{topic.learning_outcomes[0]}"
        ),
        correct_answer=topic.title,
        explanation=f"The expected answer references '{topic.title}'.",
        difficulty=topic.difficulty,
        topic_id=topic.topic_id,
        topic_name=topic.title,
    )

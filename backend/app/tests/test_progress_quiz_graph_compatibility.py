from app.agents.state import GraphState
from app.assessment.schemas import KnowledgeMap
from app.curriculum.planner import build_deterministic_curriculum
from app.curriculum.schemas import CurriculumGenerationRequest, CurriculumPlan
from app.progress.graph import apply_progress_summary_to_graph_state
from app.progress.schemas import ProgressInitializeRequest
from app.progress.service import ProgressService
from app.quiz.graph import append_quiz_result_to_graph_progress
from app.quiz.schemas import QuizAnswer, QuizGenerationRequest, QuizSubmissionRequest
from app.quiz.service import QuizService


def _curriculum() -> CurriculumPlan:
    return build_deterministic_curriculum(
        CurriculumGenerationRequest(
            goal="Learn RAG systems",
            timeline_weeks=4,
            hours_per_week=6,
            knowledge_map=KnowledgeMap(
                strong=["Python basics"],
                weak=["Embeddings"],
                missing=["Chunking", "Reranking"],
                recommended_level="beginner",
                confidence_score=0.84,
                assessment_notes=["Graph compatibility test map."],
            ),
        )
    )


async def test_progress_and_quiz_outputs_fit_graph_state() -> None:
    curriculum = _curriculum()
    graph_state = GraphState(
        user_id="demo-user",
        goal_id="goal-1",
        goal=curriculum.goal,
        timeline_weeks=curriculum.timeline_weeks,
        hours_per_week=curriculum.hours_per_week,
    )

    progress_summary = ProgressService().initialize_progress(
        ProgressInitializeRequest(curriculum=curriculum)
    ).summary
    graph_state = apply_progress_summary_to_graph_state(graph_state, progress_summary)

    quiz_service = QuizService()
    quiz = (
        await quiz_service.generate_quiz(
            QuizGenerationRequest(curriculum=curriculum, week_number=1)
        )
    ).quiz
    quiz_result = quiz_service.submit_quiz(
        quiz.quiz_id,
        QuizSubmissionRequest(
            answers=[
                QuizAnswer(
                    question_id=question.question_id,
                    answer=question.correct_answer,
                )
                for question in quiz.questions
            ]
        ),
    )
    graph_state = append_quiz_result_to_graph_progress(graph_state, quiz_result)

    assert len(graph_state.progress) == 2
    assert graph_state.metadata["progress_curriculum_id"] == curriculum.curriculum_id
    assert graph_state.metadata["latest_quiz_score"] == 1.0

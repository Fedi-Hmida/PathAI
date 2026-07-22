import type { DifficultyLevel } from "@/lib/types/curriculum";

export type QuestionType = "multiple_choice" | "short_answer" | "self_rating";

export type QuizAttemptStatus = "submitted" | "scored" | "failed";

export type QuizQuestionDTO = {
  question_id: string;
  question_type: QuestionType;
  prompt: string;
  concept_ids: string[];
  difficulty: DifficultyLevel;
  correct_answer: string;
  points: number;
  options: string[];
  rubric: string | null;
  explanation: string | null;
};

export type LearnerQuizQuestionDTO = {
  question_id: string;
  question_type: QuestionType;
  prompt: string;
  concept_ids: string[];
  difficulty: DifficultyLevel;
  points: number;
  options: string[];
};

// GET /quizzes/{quiz_id} - the learner-safe question set (no answer key),
// used to drive the take flow before any attempt exists.
export type LearnerQuizDTO = {
  quiz_id: string;
  title: string;
  questions: LearnerQuizQuestionDTO[];
  scoring_policy: { type: string; partial_credit: boolean };
};

export type QuizAnswerSubmission = {
  question_id: string;
  answer_text: string | null;
  selected_options: string[];
};

export type ConceptQuizScore = {
  concept_id: string;
  score: number;
  correct_count: number;
  total_questions: number;
};

export type QuizAttemptDTO = {
  quiz_attempt_id: string;
  quiz_id: string;
  goal_id: string;
  curriculum_id: string;
  answers: QuizAnswerSubmission[];
  total_score: number;
  correct_count: number;
  total_questions: number;
  concept_scores: ConceptQuizScore[];
  weak_concepts: string[];
  submitted_at: string;
  status: QuizAttemptStatus;
  feedback: string | null;
  adaptation_triggered: boolean;
  created_at: string;
  updated_at: string;
  schema_version: string;
};

// The backend composes `questions` from a plain `QuizQuestionDTO[]` (answer-
// keyed) only once `attempt.status === "scored"`, else from a
// `LearnerQuizQuestionDTO[]` (no answer key) - see
// `backend/app/schemas/quiz.py`'s `QuizAttemptReviewDTO`. `questions`'
// element type is a plain union rather than two full DTO variants of this
// type: the discriminant (`attempt.status`) lives one level down, so
// `isScoredQuizAttemptReview` below is the reliable way to narrow it - a
// direct `review.attempt.status === "scored"` check doesn't reliably narrow
// a nested discriminant for TS.
export type QuizAttemptReviewDTO = {
  attempt: QuizAttemptDTO;
  questions: QuizQuestionDTO[] | LearnerQuizQuestionDTO[];
};

export type ScoredQuizAttemptReviewDTO = {
  attempt: QuizAttemptDTO & { status: "scored" };
  questions: QuizQuestionDTO[];
};

export function isScoredQuizAttemptReview(
  review: QuizAttemptReviewDTO
): review is ScoredQuizAttemptReviewDTO {
  return review.attempt.status === "scored";
}

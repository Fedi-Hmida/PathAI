import { apiGet, apiPost } from "@/lib/api/client";
import type { LearnerQuizDTO, QuizAnswerSubmission, QuizAttemptReviewDTO } from "@/lib/types/quiz";

export function getLearnerQuiz(quizId: string): Promise<LearnerQuizDTO> {
  return apiGet<LearnerQuizDTO>(`/quizzes/${quizId}`);
}

export function getQuizAttemptReview(
  quizId: string,
  attemptId: string
): Promise<QuizAttemptReviewDTO> {
  return apiGet<QuizAttemptReviewDTO>(`/quizzes/${quizId}/attempts/${attemptId}`);
}

export function submitQuizAttempt(
  quizId: string,
  answers: QuizAnswerSubmission[]
): Promise<QuizAttemptReviewDTO> {
  return apiPost<QuizAttemptReviewDTO>(`/quizzes/${quizId}/attempts`, answers);
}

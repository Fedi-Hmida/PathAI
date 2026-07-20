import { apiGet } from "@/lib/api/client";
import type { QuizAttemptReviewDTO } from "@/lib/types/quiz";

export function getQuizAttemptReview(
  quizId: string,
  attemptId: string
): Promise<QuizAttemptReviewDTO> {
  return apiGet<QuizAttemptReviewDTO>(`/quizzes/${quizId}/attempts/${attemptId}`);
}

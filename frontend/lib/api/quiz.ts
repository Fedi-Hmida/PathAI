import { requestJson } from "./client";

export type QuizHistorySummary = {
  attempts: unknown[];
  average_score: number | null;
  best_score: number | null;
  curriculum_id: string;
  low_score_count: number;
};

export function getQuizHistory(curriculumId: string): Promise<QuizHistorySummary> {
  return requestJson<QuizHistorySummary>(`/quiz/${encodeURIComponent(curriculumId)}/history`);
}

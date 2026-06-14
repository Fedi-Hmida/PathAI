import { requestJson } from "./client";

export type TopicProgress = {
  status: "pending" | "in_progress" | "done" | "stuck";
  topic_id: string;
  topic_name: string;
  week_number: number;
};

export type WeekProgress = {
  completion_percentage: number;
  status: string;
  theme: string;
  topics: TopicProgress[];
  week_number: number;
};

export type ProgressAnalytics = {
  average_quiz_score?: number | null;
  completed_topic_count: number;
  completion_percentage: number;
  low_quiz_score_count: number;
  stuck_topic_count: number;
  total_topic_count: number;
};

export type CurriculumProgressSummary = {
  analytics: ProgressAnalytics;
  curriculum_id: string;
  current_week_number: number | null;
  weeks: WeekProgress[];
};

export function getProgressSummary(curriculumId: string): Promise<CurriculumProgressSummary> {
  return requestJson<CurriculumProgressSummary>(`/progress/${encodeURIComponent(curriculumId)}`);
}

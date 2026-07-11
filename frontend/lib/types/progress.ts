export type TopicProgressStatus =
  | "not_started"
  | "in_progress"
  | "completed"
  | "stuck"
  | "needs_review";

export type ProgressStatus = "not_started" | "in_progress" | "adaptation_needed" | "completed";

export type NextRecommendedAction = {
  topic_id: string | null;
  label: string;
  reason: string;
};

export type TopicProgressDTO = {
  topic_id: string;
  status: TopicProgressStatus;
  completion: number;
  last_score: number | null;
  attempt_count: number;
  completed_at: string | null;
  stuck_count: number;
  notes: string | null;
};

export type StuckEventDTO = {
  topic_id: string;
  concept_ids: string[];
  reason: string;
  created_at: string;
};

export type ProgressStateDTO = {
  progress_state_id: string;
  goal_id: string;
  curriculum_id: string;
  status: ProgressStatus;
  overall_completion: number;
  current_topic_id: string | null;
  topic_progress: TopicProgressDTO[];
  weak_concepts: string[];
  stuck_events: StuckEventDTO[];
  last_activity_at: string | null;
  next_recommended_action: NextRecommendedAction | null;
  created_at: string;
  updated_at: string;
  schema_version: string;
};

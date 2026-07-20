export type AdaptationStatus = "proposed" | "applied" | "failed";

export type AdaptationTriggerType =
  | "quiz_score_below_threshold"
  | "stuck_event_threshold"
  | "critic_score_below_threshold";

export type CurriculumChangeType =
  | "insert_topic"
  | "add_practice_exercise"
  | "reorder_topic"
  | "reduce_difficulty"
  | "add_resource"
  | "add_review_quiz"
  | "split_topic"
  | "defer_topic";

export type CurriculumChangeDTO = {
  change_type: CurriculumChangeType;
  target_week: number | null;
  affected_topic_ids: string[];
  affected_concept_ids: string[];
  reason: string;
  topic_title: string | null;
};

export type AdaptationEventDTO = {
  adaptation_event_id: string;
  goal_id: string;
  curriculum_id: string;
  trigger_type: AdaptationTriggerType;
  trigger_details: Record<string, string>;
  before_summary: string;
  after_summary: string;
  changes: CurriculumChangeDTO[];
  status: AdaptationStatus;
  quiz_attempt_id: string | null;
  stuck_event_ids: string[];
  new_curriculum_id: string | null;
  created_at: string;
  updated_at: string;
  schema_version: string;
};

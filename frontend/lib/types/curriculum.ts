export type DifficultyLevel = "beginner" | "intermediate" | "advanced";

export type CurriculumStatus =
  | "draft"
  | "under_review"
  | "active"
  | "adapted"
  | "superseded"
  | "failed";

export type CurriculumTopicDTO = {
  topic_id: string;
  title: string;
  description: string;
  concept_ids: string[];
  difficulty: DifficultyLevel;
  estimated_hours: number;
  learning_outcomes: string[];
  sequence_order: number;
  practice_task: string | null;
  assessment_checkpoint: string | null;
  resource_attachment_ids: string[];
  adaptation_origin: string | null;
};

export type CurriculumWeekDTO = {
  week_id: string;
  week_number: number;
  theme: string;
  topics: CurriculumTopicDTO[];
  estimated_hours: number;
  learning_outcomes: string[];
  milestone: string | null;
  notes: string | null;
};

export type CurriculumDTO = {
  curriculum_id: string;
  goal_id: string;
  knowledge_map_id: string;
  run_id: string;
  status: CurriculumStatus;
  title: string;
  duration_weeks: number;
  weeks: CurriculumWeekDTO[];
  target_outcomes: string[];
  assumptions: string[];
  critic_revision_attempt: number;
  version: number;
  parent_curriculum_id: string | null;
  revision_reason: string | null;
  critic_review_ids: string[];
  adaptation_event_ids: string[];
  warnings: string[];
  created_at: string;
  updated_at: string;
  schema_version: string;
};

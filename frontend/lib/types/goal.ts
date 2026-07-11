import type { GoalStatus } from "@/lib/types/dashboard";

export type LearnerProfile = {
  learner_type: string;
  strengths: string[];
  weak_areas: string[];
  time_availability_hours_per_week: number;
  desired_outcome: string;
  preferred_resource_types: string[];
  difficulty_target: string;
};

export type LearningGoalDTO = {
  goal_id: string;
  run_id: string;
  goal_text: string;
  normalized_goal_text: string;
  status: GoalStatus;
  learner_profile: LearnerProfile;
  constraints: string[];
  target_duration_weeks: number | null;
  hours_per_week: number | null;
  demo_seed_id: string | null;
  created_at: string;
  updated_at: string;
  schema_version: string;
};

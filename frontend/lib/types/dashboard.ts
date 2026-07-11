export type OrchestrationStatus =
  | "queued"
  | "running"
  | "waiting_for_user"
  | "completed"
  | "failed"
  | "cancelled";

export type ExecutionMode = "interactive" | "demo";

export type GoalStatus =
  | "created"
  | "assessment_started"
  | "curriculum_generated"
  | "active"
  | "completed"
  | "failed";

export type AssessmentStatus = "created" | "in_progress" | "completed" | "failed";

export type CriticPassStatus = "pass" | "revise" | "pass_with_warnings" | "failed";

export type EvaluationPassStatus = "pass" | "fail" | "pass_with_warnings";

export type AdaptationStatus = "proposed" | "applied" | "failed";

export type RunSummary = {
  run_id: string;
  status: OrchestrationStatus;
  mode: ExecutionMode;
  current_node: string | null;
};

export type GoalSummary = {
  goal_id: string;
  text: string;
  status: GoalStatus;
};

export type NavigationSummary = {
  artifact_ids: Record<string, string>;
};

export type AssessmentSummary = {
  assessment_session_id: string;
  status: AssessmentStatus;
  question_count: number;
  confidence: number;
  termination_reason: string | null;
};

export type KnowledgeMapSummary = {
  strong_concepts: string[];
  weak_concepts: string[];
  summary: string | null;
};

export type CurriculumWeekSummary = {
  week_number: number;
  theme: string;
  topic_titles: string[];
};

export type CurriculumSummary = {
  active_curriculum_id: string | null;
  title: string | null;
  weeks: CurriculumWeekSummary[];
};

export type ProgressSummary = {
  completion_percentage: number;
  current_topic: string | null;
  weak_concepts: string[];
  next_action_label: string | null;
  next_action_reason: string | null;
};

export type QuizSummary = {
  latest_score: number | null;
  weak_concepts: string[];
};

export type ResourcesSummary = {
  total_attached: number;
  average_relevance: number | null;
  resource_type_diversity: number | null;
};

export type AdaptationSummary = {
  recent_events: string[];
  latest_status: AdaptationStatus | null;
};

export type CriticSummary = {
  overall_score: number | null;
  pass_status: CriticPassStatus | null;
  issue_count: number;
  top_issues: string[];
};

export type EvaluationSummary = {
  overall_score: number | null;
  pass_status: EvaluationPassStatus | null;
};

export type DashboardUIFlags = {
  show_adaptation_alert: boolean;
  requires_user_input: boolean;
};

export type DashboardPayload = {
  run_summary: RunSummary;
  goal_summary: GoalSummary;
  navigation_summary: NavigationSummary;
  assessment_summary: AssessmentSummary | null;
  knowledge_map_summary: KnowledgeMapSummary | null;
  curriculum_summary: CurriculumSummary | null;
  progress_summary: ProgressSummary | null;
  quiz_summary: QuizSummary | null;
  resources_summary: ResourcesSummary | null;
  adaptation_summary: AdaptationSummary | null;
  critic_summary: CriticSummary | null;
  evaluation_summary: EvaluationSummary | null;
  ui_flags: DashboardUIFlags;
};

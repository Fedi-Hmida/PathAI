import type { ExecutionMode, OrchestrationStatus } from "@/lib/types/dashboard";

export type { ExecutionMode, OrchestrationStatus };

// Mirrors backend/app/fixtures/canonical_demo.py's RUN_ID — the only run_id
// POST /orchestration/runs ever produces (see app/api/v1/orchestration.py).
export const DEMO_RUN_ID = "run_demo_rag";

// Mirrors backend/app/orchestration/nodes.py's NODE_SEQUENCE.
export const NODE_SEQUENCE = [
  "initialize_run",
  "load_goal",
  "load_assessment",
  "load_knowledge_map",
  "load_curriculum",
  "load_resources",
  "load_critic_review",
  "load_progress",
  "load_quiz",
  "load_adaptation",
  "load_evaluation",
  "prepare_dashboard_payload",
  "complete_run",
] as const;

export type NodeName = (typeof NODE_SEQUENCE)[number];

export type OrchestrationRunStatus =
  | "created"
  | "in_progress"
  | "requires_input"
  | "completed"
  | "completed_with_warnings"
  | "failed";

export type NodeResultStatus = "success" | "failed" | "skipped" | "requires_input";

export type WorkflowError = {
  error_code: string;
  message: string;
  category: string;
  retryable: boolean;
  metadata: Record<string, unknown>;
};

export type WorkflowWarning = {
  warning_code: string;
  message: string;
  metadata: Record<string, unknown>;
};

export type WorkflowNodeEvent = {
  run_id: string;
  node_name: string;
  status: NodeResultStatus;
  attempt_count: number;
  message: string | null;
  created_at: string;
  errors: WorkflowError[];
  warnings: WorkflowWarning[];
};

// Mirrors OrchestrationRunCreate — kept for contract parity even though the
// real POST /orchestration/runs route ignores its body entirely.
export type OrchestrationRunCreate = {
  goal_id: string | null;
  mode: ExecutionMode;
  client_request_id: string | null;
};

export type OrchestrationRunDTO = {
  run_id: string;
  goal_id: string | null;
  workflow_version: string;
  status: OrchestrationRunStatus;
  current_node: string | null;
  completed_nodes: string[];
  failed_nodes: string[];
  node_events: WorkflowNodeEvent[];
  artifact_ids: Record<string, string>;
  started_at: string;
  completed_at: string | null;
  errors: WorkflowError[];
  warnings: WorkflowWarning[];
  created_at: string;
  updated_at: string;
  schema_version: string;
};

export type OrchestrationStatusResponse = {
  run_id: string;
  status: OrchestrationStatus;
  current_node: string | null;
  requires_user_input: boolean;
};

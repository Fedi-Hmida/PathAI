const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type DifficultyLevel = "beginner" | "intermediate" | "advanced";
export type TopicPriority = "high" | "medium" | "low";

export type KnowledgeMap = {
  strong: string[];
  weak: string[];
  missing: string[];
  recommended_level: DifficultyLevel;
  confidence_score: number;
  assessment_notes: string[];
};

export type CurriculumSubtopic = {
  title: string;
  estimated_hours: number;
  learning_outcome: string;
};

export type CurriculumTopic = {
  topic_id: string;
  title: string;
  priority: TopicPriority;
  difficulty: DifficultyLevel;
  estimated_hours: number;
  rationale: string;
  subtopics: CurriculumSubtopic[];
  prerequisites: string[];
  learning_outcomes: string[];
  project_or_application: boolean;
};

export type CurriculumMilestone = {
  title: string;
  description: string;
  deliverable: string;
  evaluation_hint: string;
};

export type CurriculumWeek = {
  week_number: number;
  theme: string;
  weekly_goal: string;
  milestone: CurriculumMilestone;
  estimated_hours: number;
  difficulty: DifficultyLevel;
  topics: CurriculumTopic[];
  project_or_application: boolean;
};

export type DifficultyProgression = {
  starting_level: DifficultyLevel;
  ending_level: DifficultyLevel;
  weekly_levels: DifficultyLevel[];
  rationale: string;
};

export type CurriculumValidationIssue = {
  code: string;
  message: string;
  severity: "error" | "warning";
  week_number?: number | null;
};

export type CurriculumPlan = {
  curriculum_id: string;
  user_id: string;
  goal_id?: string | null;
  assessment_session_id?: string | null;
  goal: string;
  timeline_weeks: number;
  hours_per_week: number;
  knowledge_map: KnowledgeMap;
  weeks: CurriculumWeek[];
  total_hours: number;
  difficulty_progression: DifficultyProgression;
  generation_notes: string[];
  source: "deterministic" | "mock_llm" | "real_llm";
  status: "generated" | "failed";
  validation_issues: CurriculumValidationIssue[];
  created_at: string;
  updated_at: string;
};

export type CurriculumGenerationResult = {
  curriculum: CurriculumPlan;
  validation_issues: CurriculumValidationIssue[];
};

export type CurriculumGenerationRequest = {
  user_id?: string;
  goal_id?: string | null;
  assessment_session_id?: string | null;
  goal?: string | null;
  timeline_weeks?: number | null;
  hours_per_week?: number | null;
  knowledge_map?: KnowledgeMap | null;
};

export type CurriculumValidationResponse = {
  valid: boolean;
  validation_issues: CurriculumValidationIssue[];
  message: string;
};

export class CurriculumApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string
  ) {
    super(message);
    this.name = "CurriculumApiError";
  }
}

export async function generateCurriculum(
  request: CurriculumGenerationRequest
): Promise<CurriculumGenerationResult> {
  const response = await requestJson<{ result: CurriculumGenerationResult }>("/curriculum/generate", {
    method: "POST",
    body: JSON.stringify(request)
  });
  return response.result;
}

export async function getCurriculum(curriculumId: string): Promise<CurriculumPlan> {
  const response = await requestJson<{ curriculum: CurriculumPlan }>(
    `/curriculum/${encodeURIComponent(curriculumId)}`
  );
  return response.curriculum;
}

export async function validateCurriculumRequest(
  request: CurriculumGenerationRequest
): Promise<CurriculumValidationResponse> {
  return requestJson<CurriculumValidationResponse>("/curriculum/validate", {
    method: "POST",
    body: JSON.stringify(request)
  });
}

export async function getExampleCurriculum(): Promise<CurriculumGenerationResult> {
  const response = await requestJson<{ result: CurriculumGenerationResult }>(
    "/dev/curriculum/example"
  );
  return response.result;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store"
  });

  if (!response.ok) {
    throw await toApiError(response);
  }

  return response.json() as Promise<T>;
}

async function toApiError(response: Response): Promise<CurriculumApiError> {
  try {
    const payload = (await response.json()) as { detail?: { code?: string; message?: string } };
    const detail = payload.detail;
    return new CurriculumApiError(
      detail?.message ?? "Curriculum request failed",
      response.status,
      detail?.code
    );
  } catch {
    return new CurriculumApiError("Curriculum request failed", response.status);
  }
}

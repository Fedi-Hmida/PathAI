import type { CurriculumPlan, DifficultyLevel, KnowledgeMap } from "@/lib/api/curriculum";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type DemoGoalInput = {
  goal: string;
  timeline_weeks: number;
  hours_per_week: number;
  target_level: DifficultyLevel;
  max_questions: number;
};

export type AssessmentQuestion = {
  question_id: string;
  topic: string;
  prompt: string;
  difficulty: DifficultyLevel;
  expected_concepts: string[];
  source: string;
};

export type AssessmentSession = {
  session_id: string;
  goal: string;
  timeline_weeks: number;
  hours_per_week: number;
  status: string;
};

export type StartAssessmentResponse = {
  session: AssessmentSession;
  next_question: AssessmentQuestion;
};

export type FinalAssessmentResult = {
  session_id: string;
  status: "completed";
  knowledge_map: KnowledgeMap;
};

export type FinalizeAssessmentResponse = {
  result: FinalAssessmentResult;
};

export type ResourceReference = {
  resource_id: string;
  title: string;
  url: string;
  type: string;
  source_name?: string | null;
  source_domain?: string | null;
  difficulty: DifficultyLevel;
  estimated_minutes: number;
  quality_score: number;
  why_recommended: string;
};

export type ResourceAttachment = {
  topic_id: string;
  topic: string;
  resources: ResourceReference[];
  warnings: string[];
};

export type ResourceAttachmentResponse = {
  curriculum_id: string;
  enriched_curriculum: Record<string, unknown>;
  attachments: ResourceAttachment[];
  topic_results: unknown[];
  warnings: string[];
};

export type CriticReviewResult = {
  approved: boolean;
  decision: "approved" | "rejected" | "auto_approved";
  overall_quality_score: number;
  warnings: string[];
  revision_instructions: Array<{
    category: string;
    target: string;
    instruction: string;
    severity: string;
  }>;
};

export type TopicProgress = {
  topic_id: string;
  topic_name: string;
  week_number: number;
  status: "pending" | "in_progress" | "done" | "stuck";
};

export type ProgressSummary = {
  curriculum_id: string;
  current_week_number: number | null;
  weeks: Array<{
    week_number: number;
    theme: string;
    status: string;
    completion_percentage: number;
    topics: TopicProgress[];
  }>;
  analytics: {
    completion_percentage: number;
    completed_topic_count: number;
    total_topic_count: number;
    stuck_topic_count: number;
    average_quiz_score?: number | null;
    low_quiz_score_count: number;
  };
};

export type ProgressInitializeResponse = {
  summary: ProgressSummary;
};

export type ProgressUpdateResponse = {
  summary: ProgressSummary;
};

export type QuizQuestion = {
  question_id: string;
  type: string;
  prompt: string;
  correct_answer: string;
  explanation: string;
  difficulty: string;
  topic_name: string;
  options: Array<{ option_id: string; text: string }>;
};

export type Quiz = {
  quiz_id: string;
  curriculum_id: string;
  week_number: number;
  topic_names: string[];
  questions: QuizQuestion[];
};

export type QuizGenerateResponse = {
  quiz: Quiz;
};

export type QuizResult = {
  score: number;
  passed: boolean;
  best_score: number;
  low_score_signal: boolean;
};

export type QuizHistory = {
  curriculum_id: string;
  best_score: number | null;
  average_score: number | null;
  low_score_count: number;
  attempts: unknown[];
};

export type AdaptationDecision = {
  decision: string;
  should_replan: boolean;
  trigger_reason: string;
  trigger_details: string;
  affected_weeks: Array<{ week_number: number; reason: string }>;
  affected_topics: Array<{ topic_name: string; week_number: number; reason: string }>;
};

export type AdaptationResult = {
  adaptation_id: string;
  decision: AdaptationDecision;
  critic_review?: {
    approved: boolean;
    decision: string;
    score: number;
  } | null;
  notification?: {
    title: string;
    message: string;
    change_summary: string;
  } | null;
};

export type EvaluationReport = {
  system_variant: string;
  metric_scores: Array<{ category: string; metric_name: string; score: number; passed: boolean }>;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  limitations: string[];
};

export type ServiceBackedDemoResult = {
  run_id: string;
  steps: Array<{ order: number; name: string; status: string; summary: string }>;
  critic_review: CriticReviewResult;
  quiz_result: QuizResult;
  adaptation_result: AdaptationResult;
  evaluation_report: EvaluationReport;
};

export async function startAssessment(input: DemoGoalInput): Promise<StartAssessmentResponse> {
  return requestJson<StartAssessmentResponse>("/assessment/start", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function submitAssessmentAnswer(
  sessionId: string,
  answer: string
): Promise<unknown> {
  return requestJson<unknown>(`/assessment/${encodeURIComponent(sessionId)}/answer`, {
    method: "POST",
    body: JSON.stringify({ answer })
  });
}

export async function finalizeAssessment(sessionId: string): Promise<FinalizeAssessmentResponse> {
  return requestJson<FinalizeAssessmentResponse>(
    `/assessment/${encodeURIComponent(sessionId)}/finalize`,
    { method: "POST" }
  );
}

export async function generateCurriculumFromAssessment(
  sessionId: string
): Promise<CurriculumPlan> {
  const response = await requestJson<{ result: { curriculum: CurriculumPlan } }>(
    "/curriculum/generate",
    {
      method: "POST",
      body: JSON.stringify({ assessment_session_id: sessionId })
    }
  );
  return response.result.curriculum;
}

export async function attachResources(
  curriculum: CurriculumPlan
): Promise<ResourceAttachmentResponse> {
  return requestJson<ResourceAttachmentResponse>("/resources/retrieve-for-curriculum", {
    method: "POST",
    body: JSON.stringify({ curriculum, top_k: 2 })
  });
}

export async function reviewCurriculum(
  curriculum: CurriculumPlan,
  resourceAttachment: ResourceAttachmentResponse
): Promise<CriticReviewResult> {
  return requestJson<CriticReviewResult>("/critic/review", {
    method: "POST",
    body: JSON.stringify({
      curriculum,
      resource_attachment: resourceAttachment,
      required_resources_per_topic: 1,
      revision_count: 0,
      max_revisions: 2
    })
  });
}

export async function initializeProgress(
  curriculum: CurriculumPlan
): Promise<ProgressInitializeResponse> {
  return requestJson<ProgressInitializeResponse>("/progress/initialize", {
    method: "POST",
    body: JSON.stringify({ curriculum })
  });
}

export async function updateProgress(
  summary: ProgressSummary,
  status: "done" | "stuck"
): Promise<ProgressUpdateResponse> {
  const firstWeek = summary.weeks[0];
  const firstTopic = firstWeek?.topics[0];
  if (!firstWeek || !firstTopic) {
    throw new PathAIDemoApiError("Progress summary does not contain a first topic.", 422);
  }
  return requestJson<ProgressUpdateResponse>("/progress/update", {
    method: "POST",
    body: JSON.stringify({
      curriculum_id: summary.curriculum_id,
      week_number: firstWeek.week_number,
      topic_id: firstTopic.topic_id,
      status
    })
  });
}

export async function generateQuiz(
  curriculum: CurriculumPlan,
  resourceAttachment: ResourceAttachmentResponse
): Promise<QuizGenerateResponse> {
  return requestJson<QuizGenerateResponse>("/quiz/generate", {
    method: "POST",
    body: JSON.stringify({
      curriculum,
      week_number: 1,
      resource_attachment: resourceAttachment,
      question_count: 3
    })
  });
}

export async function submitQuiz(quiz: Quiz): Promise<QuizResult> {
  return requestJson<QuizResult>(`/quiz/${encodeURIComponent(quiz.quiz_id)}/submit`, {
    method: "POST",
    body: JSON.stringify({
      answers: quiz.questions.map((question) => ({
        question_id: question.question_id,
        answer: question.correct_answer
      }))
    })
  });
}

export async function getQuizHistory(curriculumId: string): Promise<QuizHistory> {
  return requestJson<QuizHistory>(`/quiz/${encodeURIComponent(curriculumId)}/history`);
}

export async function checkAdaptation(
  curriculum: CurriculumPlan,
  progressSummary: ProgressSummary,
  quizHistory: QuizHistory
): Promise<AdaptationDecision> {
  return requestJson<AdaptationDecision>("/adapt/check", {
    method: "POST",
    body: JSON.stringify({
      curriculum,
      progress_summary: progressSummary,
      quiz_history: quizHistory,
      expected_week_number: 1
    })
  });
}

export async function runAdaptationReplan(
  curriculum: CurriculumPlan,
  progressSummary: ProgressSummary,
  quizHistory: QuizHistory,
  resourceAttachment: ResourceAttachmentResponse
): Promise<AdaptationResult> {
  return requestJson<AdaptationResult>("/adapt/replan", {
    method: "POST",
    body: JSON.stringify({
      curriculum,
      progress_summary: progressSummary,
      quiz_history: quizHistory,
      expected_week_number: 1,
      existing_resource_attachment: resourceAttachment
    })
  });
}

export async function runEvaluationSample(): Promise<EvaluationReport> {
  return requestJson<EvaluationReport>("/evaluation/run-sample", {
    method: "POST",
    body: JSON.stringify({})
  });
}

export async function runServiceBackedDemo(input: DemoGoalInput): Promise<ServiceBackedDemoResult> {
  return requestJson<ServiceBackedDemoResult>("/dev/graph/service-backed-demo-run", {
    method: "POST",
    body: JSON.stringify({
      ...input,
      assessment_answer: "Embeddings represent text as vectors for semantic retrieval.",
      quiz_question_count: 3
    })
  });
}

export class PathAIDemoApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string
  ) {
    super(message);
    this.name = "PathAIDemoApiError";
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");

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

async function toApiError(response: Response): Promise<PathAIDemoApiError> {
  try {
    const payload = (await response.json()) as {
      error?: { code?: string; message?: string };
      detail?: { code?: string; message?: string } | string;
    };
    const error = payload.error;
    const detail = payload.detail;
    if (error) {
      return new PathAIDemoApiError(error.message ?? "PathAI request failed", response.status, error.code);
    }
    if (typeof detail === "string") {
      return new PathAIDemoApiError(detail, response.status);
    }
    return new PathAIDemoApiError(
      detail?.message ?? "PathAI request failed",
      response.status,
      detail?.code
    );
  } catch {
    return new PathAIDemoApiError("PathAI request failed", response.status);
  }
}

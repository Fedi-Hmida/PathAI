import { requestJson } from "./client";

export type DifficultyLevel = "beginner" | "intermediate" | "advanced";
export type AssessmentStatus = "in_progress" | "completed" | "abandoned";
export type AssessmentSignal = "strong" | "weak" | "missing";
export type AssessmentQuestionType = "short_answer" | "multiple_choice" | "self_rating";
export type AssessmentQuestionSource = "question_bank" | "mock_llm" | "real_llm";

export type GoalIntakeRequest = {
  goal: string;
  timeline_weeks: number;
  hours_per_week: number;
  target_level: DifficultyLevel;
  user_id?: string;
  goal_id?: string | null;
  max_questions?: number;
};

export type AssessmentQuestion = {
  question_id: string;
  topic: string;
  prompt: string;
  question_type: AssessmentQuestionType;
  difficulty: DifficultyLevel;
  options: string[];
  expected_concepts: string[];
  skill_tags: string[];
  source: AssessmentQuestionSource;
};

export type AnswerEvaluation = {
  question_id: string;
  topic: string;
  difficulty: DifficultyLevel;
  answer: string;
  score: number;
  signal: AssessmentSignal;
  matched_concepts: string[];
  missing_concepts: string[];
  is_idk: boolean;
  feedback: string;
  created_at: string;
};

export type KnowledgeMap = {
  strong: string[];
  weak: string[];
  missing: string[];
  recommended_level: DifficultyLevel;
  confidence_score: number;
  assessment_notes: string[];
};

export type AssessmentProgress = {
  answered_count: number;
  asked_count: number;
  max_questions: number;
  min_questions_for_confidence: number;
  confidence_score: number;
  current_difficulty: DifficultyLevel;
  status: AssessmentStatus;
  enough_evidence: boolean;
};

export type AssessmentSession = {
  session_id: string;
  user_id: string;
  goal_id: string | null;
  goal: string;
  timeline_weeks: number;
  hours_per_week: number;
  target_level: DifficultyLevel;
  question_index: number;
  max_questions: number;
  confidence_score: number;
  status: AssessmentStatus;
  current_difficulty: DifficultyLevel;
  questions: AssessmentQuestion[];
  answers: AnswerEvaluation[];
  knowledge_map: KnowledgeMap | null;
  assessment_notes: string[];
  created_at: string;
  updated_at: string;
  progress: AssessmentProgress;
};

export type FinalAssessmentResult = {
  session_id: string;
  status: "completed";
  knowledge_map: KnowledgeMap;
  progress: AssessmentProgress;
};

export type StartAssessmentResponse = {
  session: AssessmentSession;
  next_question: AssessmentQuestion;
};

export type AssessmentSessionResponse = {
  session: AssessmentSession;
};

export type SubmitAnswerResponse = {
  session: AssessmentSession;
  evaluation: AnswerEvaluation | null;
  next_question: AssessmentQuestion | null;
  result: FinalAssessmentResult | null;
};

export type FinalizeAssessmentResponse = {
  session: AssessmentSession;
  result: FinalAssessmentResult;
};

export function startAssessment(request: GoalIntakeRequest): Promise<StartAssessmentResponse> {
  return requestJson<StartAssessmentResponse>("/assessment/start", {
    body: JSON.stringify(request),
    method: "POST"
  });
}

export function getAssessmentSession(sessionId: string): Promise<AssessmentSessionResponse> {
  return requestJson<AssessmentSessionResponse>(`/assessment/${encodeURIComponent(sessionId)}`);
}

export function submitAssessmentAnswer(
  sessionId: string,
  answer: string
): Promise<SubmitAnswerResponse> {
  return requestJson<SubmitAnswerResponse>(`/assessment/${encodeURIComponent(sessionId)}/answer`, {
    body: JSON.stringify({ answer }),
    method: "POST"
  });
}

export function finalizeAssessment(sessionId: string): Promise<FinalizeAssessmentResponse> {
  return requestJson<FinalizeAssessmentResponse>(
    `/assessment/${encodeURIComponent(sessionId)}/finalize`,
    {
      method: "POST"
    }
  );
}

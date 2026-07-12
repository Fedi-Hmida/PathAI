export type QuestionType = "multiple_choice" | "short_answer" | "self_rating";

export type DifficultyLevel = "beginner" | "intermediate" | "advanced";

export type AssessmentStatus = "created" | "in_progress" | "completed" | "failed";

export type AssessmentQuestionDTO = {
  question_id: string;
  question_type: QuestionType;
  prompt: string;
  options: string[];
  target_concepts: string[];
  difficulty: DifficultyLevel;
};

export type ConceptEvidence = {
  concept_id: string;
  score: number;
  evidence: string[];
};

export type ConceptEvidenceUpdate = {
  concept_id: string;
  score_delta: number;
  evidence: string;
};

export type AssessmentAnswerDTO = {
  answer_id: string;
  assessment_session_id: string;
  goal_id: string;
  question: AssessmentQuestionDTO;
  answer_text: string | null;
  selected_options: string[];
  self_rating: number | null;
  score: number;
  concept_scores: ConceptEvidenceUpdate[];
  feedback: string | null;
  created_at: string;
  updated_at: string;
};

export type AssessmentSessionDTO = {
  assessment_session_id: string;
  goal_id: string;
  run_id: string;
  status: AssessmentStatus;
  question_count: number;
  confidence: number;
  concept_evidence: ConceptEvidence[];
  current_question: AssessmentQuestionDTO | null;
  started_at: string;
  completed_at: string | null;
  termination_reason: string | null;
};

export type AssessmentAnswerCreate = {
  question_id: string;
  answer_text?: string | null;
  selected_options?: string[];
  self_rating?: number | null;
};

export type AssessmentAnswerResponse = {
  session: AssessmentSessionDTO;
  answer: AssessmentAnswerDTO;
};

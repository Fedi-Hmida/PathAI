export type CriticPassStatus = "pass" | "revise" | "pass_with_warnings" | "failed";

export type CriticDimensionScores = {
  coverage: number;
  pacing: number;
  resource_relevance: number;
  assessment_alignment: number;
  quiz_readiness: number | null;
};

export type CriticReviewDTO = {
  critic_review_id: string;
  goal_id: string;
  curriculum_id: string;
  run_id: string;
  overall_score: number;
  pass_status: CriticPassStatus;
  dimension_scores: CriticDimensionScores;
  strengths: string[];
  issues: string[];
  revision_recommendations: string[];
  revision_attempt: number | null;
  created_at: string;
  updated_at: string;
  schema_version: string;
};

export type ConceptClassification = "strong" | "developing" | "weak" | "missing";

export type KnowledgeMapStatus = "draft" | "active" | "superseded" | "failed";

export type ConceptMasteryDTO = {
  concept_id: string;
  label: string;
  mastery_score: number;
  classification: ConceptClassification;
  evidence: string[];
  prerequisites: string[];
  recommended_action: string | null;
  confidence: number | null;
};

export type KnowledgeMapDTO = {
  knowledge_map_id: string;
  goal_id: string;
  assessment_session_id: string;
  run_id: string;
  status: KnowledgeMapStatus;
  concepts: ConceptMasteryDTO[];
  strong_concepts: string[];
  developing_concepts: string[];
  weak_concepts: string[];
  missing_concepts: string[];
  confidence: number;
  summary: string;
  warnings: string[];
  created_at: string;
  updated_at: string;
  schema_version: string;
};

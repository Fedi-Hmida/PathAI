import type { DifficultyLevel } from "@/lib/types/curriculum";

export type ResourceType =
  | "documentation"
  | "tutorial"
  | "paper"
  | "article"
  | "video"
  | "code_example";

export type ResourceStatus = "active" | "deprecated" | "needs_review";

export type ResourceAttachmentStatus = "active" | "superseded" | "removed";

export type ResourceDTO = {
  resource_id: string;
  title: string;
  resource_type: ResourceType;
  source_name: string;
  url: string;
  topic_tags: string[];
  concept_ids: string[];
  difficulty: DifficultyLevel;
  estimated_minutes: number;
  quality_score: number;
  license_note: string;
  status: ResourceStatus;
  summary: string | null;
  author: string | null;
  published_year: number | null;
  language: string;
  freshness_score: number | null;
  created_at: string;
  updated_at: string;
  schema_version: string;
};

export type ResourceAttachmentDTO = {
  attachment_id: string;
  goal_id: string;
  curriculum_id: string;
  topic_id: string;
  resource_id: string;
  rank: number;
  relevance_score: number;
  selection_reason: string;
  quality_score_snapshot: number | null;
  diversity_category: string | null;
  status: ResourceAttachmentStatus;
  warnings: string[];
  created_at: string;
  updated_at: string;
  schema_version: string;
};

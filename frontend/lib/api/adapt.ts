import { requestJson } from "./client";

export type AdaptationHistoryItem = {
  adaptation_id: string;
  created_at?: string;
  decision?: {
    decision: string;
    should_replan: boolean;
    trigger_details: string;
    trigger_reason: string;
  };
  notification?: {
    change_summary?: string;
    message?: string;
    title?: string;
  } | null;
};

export type AdaptationHistoryResponse = {
  adaptations: AdaptationHistoryItem[];
  curriculum_id: string;
};

export function getAdaptationHistory(curriculumId: string): Promise<AdaptationHistoryResponse> {
  return requestJson<AdaptationHistoryResponse>(`/adapt/${encodeURIComponent(curriculumId)}/history`);
}

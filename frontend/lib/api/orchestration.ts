import { apiGet, apiPost } from "@/lib/api/client";
import type { OrchestrationRunDTO, OrchestrationStatusResponse } from "@/lib/types/orchestration";

export function getOrchestrationRun(runId: string): Promise<OrchestrationRunDTO> {
  return apiGet<OrchestrationRunDTO>(`/orchestration/runs/${runId}`);
}

export function getOrchestrationStatus(runId: string): Promise<OrchestrationStatusResponse> {
  return apiGet<OrchestrationStatusResponse>(`/orchestration/runs/${runId}/status`);
}

export function triggerOrchestrationRun(): Promise<OrchestrationRunDTO> {
  return apiPost<OrchestrationRunDTO>("/orchestration/runs");
}

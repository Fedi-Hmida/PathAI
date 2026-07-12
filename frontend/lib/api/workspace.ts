import { apiGet, apiPost, ApiError } from "@/lib/api/client";
import type { WorkspaceGenerationResult, WorkspaceRef } from "@/lib/types/workspace";

export async function getMyWorkspace(): Promise<WorkspaceRef | null> {
  try {
    return await apiGet<WorkspaceRef>("/me/workspace");
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export function createMyWorkspace(goalText: string): Promise<WorkspaceRef> {
  return apiPost<WorkspaceRef>("/me/workspace", { goal_text: goalText });
}

export function resetMyWorkspace(goalText: string): Promise<WorkspaceRef> {
  return apiPost<WorkspaceRef>("/me/workspace/reset", { goal_text: goalText });
}

export function generateMyWorkspace(): Promise<WorkspaceGenerationResult> {
  return apiPost<WorkspaceGenerationResult>("/me/workspace/generate");
}

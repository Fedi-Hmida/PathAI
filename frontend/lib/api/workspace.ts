import { apiGet, apiPost, ApiError } from "@/lib/api/client";
import type { WorkspaceRef } from "@/lib/types/workspace";

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

export function createMyWorkspace(): Promise<WorkspaceRef> {
  return apiPost<WorkspaceRef>("/me/workspace");
}

export function resetMyWorkspace(): Promise<WorkspaceRef> {
  return apiPost<WorkspaceRef>("/me/workspace/reset");
}

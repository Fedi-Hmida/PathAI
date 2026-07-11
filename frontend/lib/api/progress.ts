import { apiGet } from "@/lib/api/client";
import type { ProgressStateDTO } from "@/lib/types/progress";

export function getProgress(progressId: string): Promise<ProgressStateDTO> {
  return apiGet<ProgressStateDTO>(`/progress/${progressId}`);
}

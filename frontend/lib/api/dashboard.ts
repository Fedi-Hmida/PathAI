import { apiGet } from "@/lib/api/client";
import type { DashboardPayload } from "@/lib/types/dashboard";

export function getDashboard(runId: string): Promise<DashboardPayload> {
  return apiGet<DashboardPayload>(`/dashboard/${runId}`);
}

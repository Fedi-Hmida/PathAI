import { apiGet } from "@/lib/api/client";
import type { HealthStatus } from "@/lib/types/health";

export function getHealth(): Promise<HealthStatus> {
  return apiGet<HealthStatus>("/health");
}

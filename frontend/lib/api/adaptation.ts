import { apiGet } from "@/lib/api/client";
import type { AdaptationEventDTO } from "@/lib/types/adaptation";

export function getAdaptation(adaptationId: string): Promise<AdaptationEventDTO> {
  return apiGet<AdaptationEventDTO>(`/adaptations/${adaptationId}`);
}

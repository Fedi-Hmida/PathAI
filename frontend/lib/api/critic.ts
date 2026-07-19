import { apiGet } from "@/lib/api/client";
import type { CriticReviewDTO } from "@/lib/types/critic";

export function getCriticReview(criticReviewId: string): Promise<CriticReviewDTO> {
  return apiGet<CriticReviewDTO>(`/critic-reviews/${criticReviewId}`);
}

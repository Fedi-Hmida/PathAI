import { apiGet } from "@/lib/api/client";
import type { CurriculumDTO } from "@/lib/types/curriculum";

export function getCurriculum(curriculumId: string): Promise<CurriculumDTO> {
  return apiGet<CurriculumDTO>(`/curricula/${curriculumId}`);
}

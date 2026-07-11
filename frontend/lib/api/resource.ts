import { apiGet } from "@/lib/api/client";
import type { ResourceAttachmentDTO, ResourceDTO } from "@/lib/types/resource";

export function getResourceAttachmentsByCurriculum(
  curriculumId: string
): Promise<ResourceAttachmentDTO[]> {
  return apiGet<ResourceAttachmentDTO[]>(`/resources/by-curriculum/${curriculumId}`);
}

export function getResource(resourceId: string): Promise<ResourceDTO> {
  return apiGet<ResourceDTO>(`/resources/${resourceId}`);
}

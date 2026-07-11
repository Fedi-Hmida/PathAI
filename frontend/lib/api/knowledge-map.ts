import { apiGet } from "@/lib/api/client";
import type { KnowledgeMapDTO } from "@/lib/types/knowledge-map";

export function getKnowledgeMap(knowledgeMapId: string): Promise<KnowledgeMapDTO> {
  return apiGet<KnowledgeMapDTO>(`/knowledge-maps/${knowledgeMapId}`);
}

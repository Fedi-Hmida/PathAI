import type { CurriculumTopicDTO } from "@/lib/types/curriculum";
import type { ResourceAttachmentDTO, ResourceDTO, ResourceType } from "@/lib/types/resource";

export const TOTAL_RESOURCE_TYPE_COUNT = 8 satisfies number;

export type ResourceCoverage = {
  topicsCovered: number;
  topicsTotal: number;
  averageRelevance: number | null;
  distinctResourceTypeCount: number;
};

export function computeResourceCoverage(
  topics: CurriculumTopicDTO[],
  attachments: ResourceAttachmentDTO[],
  resourcesById: Map<string, ResourceDTO>
): ResourceCoverage {
  const coveredTopicIds = new Set(attachments.map((attachment) => attachment.topic_id));
  const topicsCovered = topics.filter((topic) => coveredTopicIds.has(topic.topic_id)).length;

  const averageRelevance =
    attachments.length === 0
      ? null
      : attachments.reduce((sum, attachment) => sum + attachment.relevance_score, 0) /
        attachments.length;

  const distinctResourceTypes = new Set<ResourceType>();
  for (const attachment of attachments) {
    const resource = resourcesById.get(attachment.resource_id);
    if (resource) {
      distinctResourceTypes.add(resource.resource_type);
    }
  }

  return {
    topicsCovered,
    topicsTotal: topics.length,
    averageRelevance,
    distinctResourceTypeCount: distinctResourceTypes.size,
  };
}

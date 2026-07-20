import { ResourceCard } from "@/components/resources/resource-card";
import type { CurriculumTopicDTO, DifficultyLevel } from "@/lib/types/curriculum";
import type { ResourceAttachmentDTO, ResourceDTO, ResourceType } from "@/lib/types/resource";

export type ResourceShelfItem = {
  attachment: ResourceAttachmentDTO;
  resource: ResourceDTO;
};

export interface ResourceShelfProps {
  topic: CurriculumTopicDTO;
  items: ResourceShelfItem[];
  activeTypes: ResourceType[];
  activeDifficulties: DifficultyLevel[];
}

export function ResourceShelf({ topic, items, activeTypes, activeDifficulties }: ResourceShelfProps) {
  const visibleItems = items.filter(
    ({ resource }) =>
      (activeTypes.length === 0 || activeTypes.includes(resource.resource_type)) &&
      (activeDifficulties.length === 0 || activeDifficulties.includes(resource.difficulty))
  );

  return (
    <section>
      <div className="mb-3.5 flex items-baseline gap-2.5">
        <h2 className="text-foreground text-[17px] font-medium">{topic.title}</h2>
        {items.length > 0 ? (
          <span className="text-tertiary text-xs">
            {items.length} resource{items.length === 1 ? "" : "s"}
          </span>
        ) : null}
      </div>

      {items.length === 0 ? (
        <p className="text-muted-foreground border-border border-t border-dashed py-4.5 text-[13.5px]">
          No resources attached yet.
        </p>
      ) : visibleItems.length === 0 ? (
        <p className="text-muted-foreground border-border border-t border-dashed py-4.5 text-[13.5px]">
          No resources match the selected filters.
        </p>
      ) : (
        <div className="-mx-1 flex overflow-x-auto px-1 pb-2.5">
          {visibleItems.map(({ attachment, resource }) => (
            <div key={attachment.attachment_id} className="px-1">
              <ResourceCard attachment={attachment} resource={resource} />
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

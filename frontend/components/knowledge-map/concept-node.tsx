import { ProgressRing } from "@/components/dashboard/progress-ring";
import { cn } from "@/lib/utils";
import type { ConceptMasteryDTO } from "@/lib/types/knowledge-map";
import { CLASSIFICATION_CONFIG } from "@/components/knowledge-map/classification-legend";
import type { GraphNode } from "@/components/knowledge-map/graph-layout";

const NODE_DIAMETER = 60;

type ConceptNodeProps = {
  concept: ConceptMasteryDTO;
  position: GraphNode;
  selected: boolean;
  dimmed: boolean;
  onSelect: (conceptId: string) => void;
};

export function ConceptNode({ concept, position, selected, dimmed, onSelect }: ConceptNodeProps) {
  const config = CLASSIFICATION_CONFIG[concept.classification];

  return (
    <button
      type="button"
      onClick={() => onSelect(concept.concept_id)}
      title={concept.label}
      style={{
        left: position.x,
        top: position.y,
        transform: "translate(-50%, -50%)",
      }}
      className={cn(
        "absolute flex w-24 flex-col items-center gap-1.5 rounded-xl px-1 py-2 transition-opacity",
        dimmed && "opacity-30"
      )}
    >
      <div
        className={cn(
          "flex items-center justify-center rounded-full",
          selected && "ring-brand ring-offset-background ring-2 ring-offset-2",
          config.dashed && "border-2 border-dashed"
        )}
        style={{
          width: NODE_DIAMETER,
          height: NODE_DIAMETER,
          borderColor: config.dashed ? config.ringColor : undefined,
        }}
      >
        <ProgressRing
          value={Math.round(concept.mastery_score * 100)}
          size={config.dashed ? NODE_DIAMETER - 8 : NODE_DIAMETER}
          strokeWidth={5}
          hideLabel
          indicatorColor={config.ringColor}
          label={`${concept.label} mastery`}
        />
      </div>
      <span className="text-foreground line-clamp-2 text-center text-[11px] leading-tight font-medium">
        {concept.label}
      </span>
    </button>
  );
}

import { createElement } from "react";

import { ProgressRing } from "@/components/dashboard/progress-ring";
import { cn } from "@/lib/utils";
import type { ConceptMasteryDTO } from "@/lib/types/knowledge-map";
import { CLASSIFICATION_CONFIG } from "@/components/knowledge-map/classification-legend";
import { iconForConcept } from "@/components/knowledge-map/concept-icon";
import type { GraphNode } from "@/components/knowledge-map/graph-layout";

const NODE_DIAMETER = 66;
const INNER_INSET = 7;

type ConceptNodeProps = {
  concept: ConceptMasteryDTO;
  position: GraphNode;
  selected: boolean;
  dimmed: boolean;
  onSelect: (conceptId: string) => void;
};

export function ConceptNode({ concept, position, selected, dimmed, onSelect }: ConceptNodeProps) {
  const config = CLASSIFICATION_CONFIG[concept.classification];
  const icon = createElement(iconForConcept(concept), {
    className: "size-4.5",
    style: { color: config.ringColor },
    strokeWidth: 2,
  });

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
        "absolute flex w-28 flex-col items-center gap-2 rounded-xl px-1 py-2 transition-opacity",
        dimmed && "opacity-25"
      )}
    >
      <div className="relative" style={{ width: NODE_DIAMETER, height: NODE_DIAMETER }}>
        {/* Mastery arc */}
        <ProgressRing
          value={Math.round(concept.mastery_score * 100)}
          size={NODE_DIAMETER}
          strokeWidth={4}
          hideLabel
          indicatorColor={config.ringColor}
          label={`${concept.label} mastery`}
        />
        {/* Filled disc + themed icon inside the ring */}
        <div
          className={cn(
            "bg-surface-sunken absolute flex items-center justify-center rounded-full",
            config.dashed && "border-2 border-dashed bg-transparent",
            selected && "shadow-[0_0_0_6px_var(--brand-tint)]"
          )}
          style={{
            inset: INNER_INSET,
            borderColor: config.dashed ? config.ringColor : undefined,
          }}
        >
          {icon}
        </div>
        {selected ? (
          <span
            className="ring-brand pointer-events-none absolute rounded-full ring-2"
            style={{ inset: -4 }}
          />
        ) : null}
      </div>
      <span
        className={cn(
          "line-clamp-2 text-center text-[11px] leading-tight font-medium",
          selected ? "text-brand" : "text-foreground"
        )}
      >
        {concept.label}
      </span>
    </button>
  );
}

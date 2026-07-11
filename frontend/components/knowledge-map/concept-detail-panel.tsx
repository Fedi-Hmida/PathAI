import { Lightbulb } from "lucide-react";

import { ProgressRing } from "@/components/dashboard/progress-ring";
import { CLASSIFICATION_CONFIG } from "@/components/knowledge-map/classification-legend";
import { cn } from "@/lib/utils";
import type { ConceptMasteryDTO } from "@/lib/types/knowledge-map";

type ConceptDetailPanelProps = {
  concept: ConceptMasteryDTO;
  conceptsById: Map<string, ConceptMasteryDTO>;
  onSelectConcept: (conceptId: string) => void;
};

export function ConceptDetailPanel({ concept, conceptsById, onSelectConcept }: ConceptDetailPanelProps) {
  const config = CLASSIFICATION_CONFIG[concept.classification];

  return (
    <div className="border-border bg-card flex flex-1 flex-col gap-5 rounded-2xl border p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <span
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold",
              config.tintClass,
              config.textClass
            )}
          >
            {config.label}
          </span>
          <h3 className="font-goal text-foreground mt-2 text-lg font-medium">{concept.label}</h3>
        </div>
        <ProgressRing
          value={Math.round(concept.mastery_score * 100)}
          size={56}
          strokeWidth={5}
          indicatorColor={config.ringColor}
          label={`${concept.label} mastery`}
        />
      </div>

      <div className="flex items-center justify-between text-[13px]">
        <span className="text-muted-foreground">Confidence</span>
        <span className="font-tabular text-foreground font-medium">
          {concept.confidence !== null ? `${Math.round(concept.confidence * 100)}%` : "—"}
        </span>
      </div>

      <div className="flex flex-col gap-1.5">
        <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
          Evidence
        </span>
        {concept.evidence.length > 0 ? (
          <ul className="flex flex-col gap-1.5">
            {concept.evidence.map((item) => (
              <li key={item} className="text-muted-foreground text-[13px] leading-relaxed">
                {item}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-muted-foreground text-[13px]">No evidence recorded.</p>
        )}
      </div>

      {concept.recommended_action ? (
        <div className="bg-surface-sunken flex items-start gap-3 rounded-xl px-4 py-3.5">
          <Lightbulb className="text-brand mt-0.5 size-4 flex-none" />
          <div>
            <div className="text-brand mb-1 text-[11px] font-bold tracking-wide uppercase">
              Recommended action
            </div>
            <div className="text-muted-foreground text-[13px] leading-relaxed">
              {concept.recommended_action}
            </div>
          </div>
        </div>
      ) : null}

      <div className="flex flex-col gap-1.5">
        <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
          Prerequisites
        </span>
        {concept.prerequisites.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {concept.prerequisites.map((prerequisiteId) => {
              const prerequisite = conceptsById.get(prerequisiteId);
              if (!prerequisite) {
                return (
                  <span
                    key={prerequisiteId}
                    className="bg-surface-sunken text-tertiary rounded-full px-3 py-1 text-xs font-medium"
                  >
                    {prerequisiteId}
                  </span>
                );
              }
              return (
                <button
                  key={prerequisiteId}
                  type="button"
                  onClick={() => onSelectConcept(prerequisiteId)}
                  className="bg-surface-sunken text-muted-foreground hover:text-brand rounded-full px-3 py-1 text-xs font-medium"
                >
                  {prerequisite.label}
                </button>
              );
            })}
          </div>
        ) : (
          <p className="text-muted-foreground text-[13px]">None.</p>
        )}
      </div>
    </div>
  );
}

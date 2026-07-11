import { cn } from "@/lib/utils";
import type { ConceptClassification, ConceptMasteryDTO } from "@/lib/types/knowledge-map";

export const CLASSIFICATION_ORDER: ConceptClassification[] = [
  "strong",
  "developing",
  "weak",
  "missing",
];

export const CLASSIFICATION_CONFIG: Record<
  ConceptClassification,
  { label: string; ringColor: string; tintClass: string; textClass: string; dashed: boolean }
> = {
  strong: {
    label: "Strong",
    ringColor: "var(--success)",
    tintClass: "bg-success-tint",
    textClass: "text-success",
    dashed: false,
  },
  developing: {
    label: "Developing",
    ringColor: "var(--brand)",
    tintClass: "bg-brand-tint",
    textClass: "text-brand",
    dashed: false,
  },
  weak: {
    label: "Weak",
    ringColor: "var(--warning)",
    tintClass: "bg-warning-tint",
    textClass: "text-warning",
    dashed: false,
  },
  missing: {
    label: "Missing",
    ringColor: "var(--text-tertiary)",
    tintClass: "bg-surface-sunken",
    textClass: "text-tertiary",
    dashed: true,
  },
};

export function countByClassification(
  concepts: ConceptMasteryDTO[]
): Record<ConceptClassification, number> {
  const counts: Record<ConceptClassification, number> = {
    strong: 0,
    developing: 0,
    weak: 0,
    missing: 0,
  };
  for (const concept of concepts) {
    counts[concept.classification] += 1;
  }
  return counts;
}

type ClassificationLegendProps = {
  concepts: ConceptMasteryDTO[];
  activeClassifications: Set<ConceptClassification>;
  onToggleClassification: (classification: ConceptClassification) => void;
};

export function ClassificationLegend({
  concepts,
  activeClassifications,
  onToggleClassification,
}: ClassificationLegendProps) {
  const counts = countByClassification(concepts);

  return (
    <div className="flex flex-wrap items-center gap-2">
      {CLASSIFICATION_ORDER.map((classification) => {
        const config = CLASSIFICATION_CONFIG[classification];
        const count = counts[classification];
        const active = activeClassifications.has(classification);
        return (
          <button
            key={classification}
            type="button"
            onClick={() => onToggleClassification(classification)}
            disabled={count === 0}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-opacity",
              config.tintClass,
              config.textClass,
              !active && "opacity-40",
              count === 0 && "cursor-default opacity-25"
            )}
          >
            <span
              className={cn("size-2.5 rounded-full", config.dashed && "border border-dashed")}
              style={{
                backgroundColor: config.dashed ? "transparent" : config.ringColor,
                borderColor: config.dashed ? config.ringColor : undefined,
              }}
            />
            {config.label}
            <span className="font-tabular">{count}</span>
          </button>
        );
      })}
    </div>
  );
}

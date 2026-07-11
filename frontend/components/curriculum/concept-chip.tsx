import { ProgressRing } from "@/components/dashboard/progress-ring";
import type { ConceptMasteryDTO } from "@/lib/types/knowledge-map";

function formatConceptLabel(conceptId: string): string {
  return conceptId
    .split("_")
    .filter(Boolean)
    .map((word) => word[0]!.toUpperCase() + word.slice(1))
    .join(" ");
}

function masteryColor(score: number): string {
  if (score >= 0.8) return "var(--success)";
  if (score >= 0.5) return "var(--brand)";
  if (score >= 0.25) return "var(--warning)";
  return "var(--danger)";
}

type ConceptChipProps = {
  conceptId: string;
  concept: ConceptMasteryDTO | null;
};

export function ConceptChip({ conceptId, concept }: ConceptChipProps) {
  const label = concept?.label ?? formatConceptLabel(conceptId);
  const scorePercent = concept ? Math.round(concept.mastery_score * 100) : null;

  return (
    <span className="bg-surface-sunken text-muted-foreground inline-flex items-center gap-2 rounded-full py-1 pr-3 pl-1.5 text-xs font-medium">
      {concept ? (
        <ProgressRing
          value={scorePercent!}
          size={20}
          strokeWidth={3}
          hideLabel
          indicatorColor={masteryColor(concept.mastery_score)}
          label={`${label} mastery`}
        />
      ) : null}
      <span>{label}</span>
      {scorePercent !== null ? (
        <span className="font-tabular text-tertiary">{scorePercent}%</span>
      ) : null}
    </span>
  );
}

import { cn, formatConceptLabel } from "@/lib/utils";
import type { ConceptEvidence } from "@/lib/types/assessment";

type ConceptStatus = "confident" | "probing" | "not_yet";

function statusFor(score: number): ConceptStatus {
  if (score >= 0.7) return "confident";
  if (score >= 0.4) return "probing";
  return "not_yet";
}

const STATUS_CONFIG: Record<ConceptStatus, { label: string; pill: string; dot: string; bar: string }> = {
  confident: {
    label: "Confident",
    pill: "bg-success-tint text-success",
    dot: "bg-success",
    bar: "bg-success",
  },
  probing: {
    label: "Probing",
    pill: "bg-warning-tint text-warning",
    dot: "bg-warning",
    bar: "bg-warning",
  },
  not_yet: {
    label: "Not yet",
    pill: "bg-surface-sunken text-tertiary",
    dot: "bg-border",
    bar: "bg-border",
  },
};

type ConceptSidebarProps = {
  conceptEvidence: ConceptEvidence[];
};

export function ConceptSidebar({ conceptEvidence }: ConceptSidebarProps) {
  return (
    <div className="border-border bg-card sticky top-6 rounded-2xl border p-6 shadow-sm">
      <div className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
        Concepts assessed so far
      </div>

      {conceptEvidence.length === 0 ? (
        <p className="text-muted-foreground mt-4 text-sm">
          Your first answer will start narrowing in on concepts.
        </p>
      ) : (
        <div className="mt-5 flex flex-col gap-5">
          {conceptEvidence.map((concept) => {
            const status = statusFor(concept.score);
            const config = STATUS_CONFIG[status];
            const percent = Math.round(Math.max(0, Math.min(1, concept.score)) * 100);
            return (
              <div key={concept.concept_id}>
                <div className="mb-1.5 flex items-center justify-between gap-2">
                  <span className="text-foreground text-sm font-medium">
                    {formatConceptLabel(concept.concept_id)}
                  </span>
                  <span
                    className={cn(
                      "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold whitespace-nowrap",
                      config.pill
                    )}
                  >
                    <span className={cn("size-1.5 flex-none rounded-full", config.dot)} />
                    {config.label}
                  </span>
                </div>
                <div className="bg-surface-sunken relative h-[5px] overflow-hidden rounded-full">
                  <div
                    className={cn("absolute inset-y-0 left-0 rounded-full transition-all", config.bar)}
                    style={{ width: `${percent}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}

      <p className="text-tertiary border-border mt-6 border-t pt-5 text-xs leading-relaxed">
        Each answer narrows the next question&apos;s difficulty and topic.
      </p>
    </div>
  );
}

import Link from "next/link";
import { AlertTriangle, CheckCircle2 } from "lucide-react";

import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { KnowledgeMapSummary } from "@/lib/types/dashboard";

function formatConceptLabel(conceptId: string): string {
  return conceptId
    .split("_")
    .filter(Boolean)
    .map((word) => word[0]!.toUpperCase() + word.slice(1))
    .join(" ");
}

function ConceptChip({ conceptId, tone }: { conceptId: string; tone: "success" | "warning" }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium",
        tone === "success" ? "bg-success-tint text-success" : "bg-warning-tint text-warning"
      )}
    >
      {tone === "success" ? (
        <CheckCircle2 className="size-3" />
      ) : (
        <AlertTriangle className="size-3" />
      )}
      {formatConceptLabel(conceptId)}
    </span>
  );
}

type KnowledgeMapCardProps = {
  knowledgeMapSummary: KnowledgeMapSummary | null;
  assessmentId?: string | null;
  knowledgeMapId?: string | null;
};

export function KnowledgeMapCard({
  knowledgeMapSummary,
  assessmentId = null,
  knowledgeMapId = null,
}: KnowledgeMapCardProps) {
  return (
    <Card className="flex-[2_1_520px] py-6">
      <CardHeader>
        <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
          Knowledge map
        </span>
        <CardTitle className="font-goal text-lg font-medium">Where you stand</CardTitle>
        {assessmentId !== null || knowledgeMapId !== null ? (
          <CardAction className="flex flex-col items-end gap-1">
            {knowledgeMapId !== null ? (
              <Link href={`/knowledge-map/${knowledgeMapId}`} className="text-brand hover:underline text-[13px] font-medium">
                View full map
              </Link>
            ) : null}
            {assessmentId !== null ? (
              <Link href={`/assessment/${assessmentId}`} className="text-brand hover:underline text-[13px] font-medium">
                View assessment
              </Link>
            ) : null}
          </CardAction>
        ) : null}
      </CardHeader>
      <CardContent>
        {knowledgeMapSummary === null ? (
          <p className="text-muted-foreground text-sm">
            No knowledge map yet — it will appear once the diagnostic assessment completes.
          </p>
        ) : (
          <div className="flex flex-col gap-6">
            <div className="flex flex-col gap-2">
              <div className="text-success flex items-center gap-1.5 text-xs font-semibold">
                <CheckCircle2 className="size-3.5" />
                Strong concepts
              </div>
              {knowledgeMapSummary.strong_concepts.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {knowledgeMapSummary.strong_concepts.map((conceptId) => (
                    <ConceptChip key={conceptId} conceptId={conceptId} tone="success" />
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-sm">No strong concepts identified yet.</p>
              )}
            </div>

            <div className="flex flex-col gap-2">
              <div className="text-warning flex items-center gap-1.5 text-xs font-semibold">
                <AlertTriangle className="size-3.5" />
                Needs work
              </div>
              {knowledgeMapSummary.weak_concepts.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {knowledgeMapSummary.weak_concepts.map((conceptId) => (
                    <ConceptChip key={conceptId} conceptId={conceptId} tone="warning" />
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-sm">No weak concepts identified.</p>
              )}
            </div>

            {knowledgeMapSummary.summary ? (
              <p className="text-muted-foreground border-t pt-4 text-sm leading-relaxed">
                {knowledgeMapSummary.summary}
              </p>
            ) : null}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

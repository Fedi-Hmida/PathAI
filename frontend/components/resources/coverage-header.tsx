import { TOTAL_RESOURCE_TYPE_COUNT } from "@/components/resources/coverage-math";
import { scoreBand } from "@/lib/score-band";
import { cn } from "@/lib/utils";

const TONE_TEXT_CLASS: Record<ReturnType<typeof scoreBand>, string> = {
  success: "text-success",
  brand: "text-brand",
  warning: "text-warning",
};

export interface CoverageHeaderProps {
  topicsCovered: number;
  topicsTotal: number;
  averageRelevance: number | null;
  distinctResourceTypeCount: number;
}

export function CoverageHeader({
  topicsCovered,
  topicsTotal,
  averageRelevance,
  distinctResourceTypeCount,
}: CoverageHeaderProps) {
  const typeCoverageRatio = distinctResourceTypeCount / TOTAL_RESOURCE_TYPE_COUNT;

  return (
    <div className="border-border flex flex-wrap items-center gap-7 border-b pb-7">
      <span className="text-foreground text-[15px]">
        {topicsCovered} of {topicsTotal} topic{topicsTotal === 1 ? "" : "s"} covered
      </span>

      <div className="bg-border h-7.5 w-px flex-none" />

      <div className="flex min-w-0 flex-col gap-0.5">
        <span className="text-tertiary text-[11px] font-semibold tracking-wide uppercase">
          Average relevance
        </span>
        <span
          className={cn(
            "font-mono text-base font-medium",
            averageRelevance === null ? "text-muted-foreground" : TONE_TEXT_CLASS[scoreBand(averageRelevance)]
          )}
        >
          {averageRelevance === null ? "—" : averageRelevance.toFixed(2)}
        </span>
      </div>

      <div className="flex min-w-0 flex-col gap-0.5">
        <span className="text-tertiary text-[11px] font-semibold tracking-wide uppercase">
          Format diversity
        </span>
        <span className={cn("font-mono text-base font-medium", TONE_TEXT_CLASS[scoreBand(typeCoverageRatio)])}>
          {distinctResourceTypeCount} of {TOTAL_RESOURCE_TYPE_COUNT} types
        </span>
      </div>
    </div>
  );
}

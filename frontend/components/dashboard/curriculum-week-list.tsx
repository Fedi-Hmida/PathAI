import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { CurriculumSummary, CurriculumWeekSummary, NavigationSummary } from "@/lib/types/dashboard";

export function isCurrentWeek(
  week: CurriculumWeekSummary,
  currentTopic: string | null
): boolean {
  return currentTopic != null && week.topic_titles.includes(currentTopic);
}

// navigation_summary.artifact_ids omits keys whose value is null
// (see _artifact_ids() in backend/app/services/dashboard.py), so only
// the params that are actually present get forwarded to the detail page.
function buildWeekHref(
  curriculumId: string,
  weekNumber: number,
  artifactIds: Record<string, string>
): string {
  const params = new URLSearchParams({ week: String(weekNumber) });
  if (artifactIds.progress_state_id) {
    params.set("progressId", artifactIds.progress_state_id);
  }
  if (artifactIds.knowledge_map_id) {
    params.set("knowledgeMapId", artifactIds.knowledge_map_id);
  }
  return `/curriculum/${curriculumId}?${params.toString()}`;
}

type CurriculumWeekListProps = {
  curriculumSummary: CurriculumSummary | null;
  currentTopic: string | null;
  navigationSummary: NavigationSummary;
};

export function CurriculumWeekList({
  curriculumSummary,
  currentTopic,
  navigationSummary,
}: CurriculumWeekListProps) {
  const weeks = curriculumSummary?.weeks ?? [];
  const curriculumId = curriculumSummary?.active_curriculum_id ?? null;

  return (
    <Card className="py-6">
      <CardHeader>
        <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
          Curriculum
        </span>
        <CardTitle className="font-goal text-lg font-medium">
          {curriculumSummary?.title ?? "Week-by-week plan"}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {weeks.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            No curriculum has been generated for this run yet.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {weeks.map((week) => {
              const active = isCurrentWeek(week, currentTopic);
              const cardClassName = cn(
                "flex flex-col gap-2.5 rounded-xl border p-4",
                active ? "border-brand bg-brand-tint" : "border-border"
              );
              const cardContent = (
                <>
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "flex size-5.5 flex-none items-center justify-center rounded-full text-[11px] font-bold text-white",
                        active ? "bg-brand" : "bg-tertiary"
                      )}
                    >
                      {week.week_number}
                    </span>
                    <span className="text-tertiary text-[11px] font-semibold tracking-wide uppercase">
                      Week {week.week_number}
                    </span>
                  </div>
                  <div className="font-goal text-foreground text-[15px] font-medium">
                    {week.theme}
                  </div>
                  {week.topic_titles.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {week.topic_titles.map((title) => (
                        <span
                          key={title}
                          className="bg-surface-sunken text-muted-foreground rounded-full px-2.5 py-1 text-xs font-medium"
                        >
                          {title}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </>
              );

              if (curriculumId === null) {
                return (
                  <div key={week.week_number} className={cardClassName}>
                    {cardContent}
                  </div>
                );
              }

              return (
                <Link
                  key={week.week_number}
                  href={buildWeekHref(curriculumId, week.week_number, navigationSummary.artifact_ids)}
                  className={cn(cardClassName, "hover:border-brand transition-colors")}
                >
                  {cardContent}
                </Link>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

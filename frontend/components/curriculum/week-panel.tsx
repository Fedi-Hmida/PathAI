import { ArrowLeft, ArrowRight, Flag } from "lucide-react";

import { TopicRow } from "@/components/curriculum/topic-row";
import type { CurriculumWeekDTO } from "@/lib/types/curriculum";
import type { ConceptMasteryDTO } from "@/lib/types/knowledge-map";
import type { ProgressStateDTO } from "@/lib/types/progress";
import type { ResourceAttachmentDTO, ResourceDTO } from "@/lib/types/resource";

type WeekPanelProps = {
  week: CurriculumWeekDTO;
  prevWeek: CurriculumWeekDTO | null;
  nextWeek: CurriculumWeekDTO | null;
  onNavigateWeek: (weekNumber: number) => void;
  progress: ProgressStateDTO | null;
  conceptsById: Map<string, ConceptMasteryDTO> | null;
  attachmentsByTopicId: Map<string, ResourceAttachmentDTO[]>;
  resourceTitles: Map<string, ResourceDTO>;
  onRequestResourceTitles: (resourceIds: string[]) => void;
};

export function WeekPanel({
  week,
  prevWeek,
  nextWeek,
  onNavigateWeek,
  progress,
  conceptsById,
  attachmentsByTopicId,
  resourceTitles,
  onRequestResourceTitles,
}: WeekPanelProps) {
  const progressByTopic = new Map(
    (progress?.topic_progress ?? []).map((entry) => [entry.topic_id, entry])
  );

  return (
    <div className="flex flex-col gap-6">
      <div>
        <div className="text-tertiary font-mono text-[13px] font-semibold">
          Week {week.week_number}
        </div>
        <h1 className="font-goal text-foreground mt-1 text-[30px] leading-tight font-medium">
          {week.theme}
        </h1>
        <div className="mt-3 flex flex-wrap items-center gap-3.5">
          <span className="text-muted-foreground font-mono text-[13px]">
            {week.estimated_hours}h estimated
          </span>
          {week.milestone ? (
            <span className="bg-brand-tint text-brand inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[13px] font-semibold">
              <Flag className="size-3" />
              Milestone: {week.milestone}
            </span>
          ) : null}
        </div>
        {week.notes ? (
          <p className="text-tertiary mt-3 max-w-xl text-[13px] leading-relaxed italic">
            {week.notes}
          </p>
        ) : null}
      </div>

      <div className="flex flex-col gap-3">
        {week.topics.map((topic) => (
          <TopicRow
            key={topic.topic_id}
            topic={topic}
            progress={progressByTopic.get(topic.topic_id) ?? null}
            conceptsById={conceptsById}
            attachments={attachmentsByTopicId.get(topic.topic_id) ?? []}
            resourceTitles={resourceTitles}
            onRequestResourceTitles={onRequestResourceTitles}
          />
        ))}
      </div>

      <div className="border-border flex items-center justify-between gap-5 border-t pt-5">
        {prevWeek ? (
          <button
            type="button"
            onClick={() => onNavigateWeek(prevWeek.week_number)}
            className="text-muted-foreground hover:text-brand inline-flex items-center gap-1.5 text-left text-[13px]"
          >
            <ArrowLeft className="size-3.5 flex-none" />
            Week {prevWeek.week_number}: {prevWeek.theme}
          </button>
        ) : (
          <span />
        )}
        {nextWeek ? (
          <button
            type="button"
            onClick={() => onNavigateWeek(nextWeek.week_number)}
            className="text-muted-foreground hover:text-brand inline-flex items-center gap-1.5 text-right text-[13px]"
          >
            Week {nextWeek.week_number}: {nextWeek.theme}
            <ArrowRight className="size-3.5 flex-none" />
          </button>
        ) : (
          <span />
        )}
      </div>
    </div>
  );
}

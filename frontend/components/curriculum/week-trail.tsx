"use client";

import { Check } from "lucide-react";

import { cn } from "@/lib/utils";
import type { CurriculumWeekDTO } from "@/lib/types/curriculum";
import type { ProgressStateDTO } from "@/lib/types/progress";

const MIN_STONE_SIZE = 32;
const MAX_STONE_SIZE = 48;

type StoneStatus = "completed" | "current" | "unknown";

function deriveWeekStatus(
  week: CurriculumWeekDTO,
  progress: ProgressStateDTO | null
): StoneStatus {
  if (progress === null) {
    return "unknown";
  }
  const topicIds = new Set(week.topics.map((topic) => topic.topic_id));
  if (progress.current_topic_id !== null && topicIds.has(progress.current_topic_id)) {
    return "current";
  }
  const progressByTopic = new Map(progress.topic_progress.map((entry) => [entry.topic_id, entry]));
  const allCompleted = week.topics.every(
    (topic) => progressByTopic.get(topic.topic_id)?.status === "completed"
  );
  return allCompleted ? "completed" : "unknown";
}

function stoneSize(week: CurriculumWeekDTO, minHours: number, maxHours: number): number {
  if (maxHours === minHours) {
    return (MIN_STONE_SIZE + MAX_STONE_SIZE) / 2;
  }
  const ratio = (week.estimated_hours - minHours) / (maxHours - minHours);
  return MIN_STONE_SIZE + ratio * (MAX_STONE_SIZE - MIN_STONE_SIZE);
}

type WeekTrailProps = {
  weeks: CurriculumWeekDTO[];
  progress: ProgressStateDTO | null;
  selectedWeekNumber: number;
  onSelectWeek: (weekNumber: number) => void;
};

export function WeekTrail({ weeks, progress, selectedWeekNumber, onSelectWeek }: WeekTrailProps) {
  const hours = weeks.map((week) => week.estimated_hours);
  const minHours = Math.min(...hours);
  const maxHours = Math.max(...hours);

  return (
    <div className="relative flex items-center gap-7 overflow-x-auto px-2 pt-3 pb-2">
      <div className="bg-border absolute top-1/2 right-6 left-6 h-px -translate-y-1/2" />
      {weeks.map((week) => {
        const status = deriveWeekStatus(week, progress);
        const size = stoneSize(week, minHours, maxHours);
        const selected = week.week_number === selectedWeekNumber;

        return (
          <button
            key={week.week_number}
            type="button"
            title={`Week ${week.week_number}: ${week.theme}`}
            onClick={() => onSelectWeek(week.week_number)}
            className={cn(
              "relative z-10 flex flex-none items-center justify-center rounded-full transition-transform",
              status === "completed" && "bg-success",
              status === "current" && "bg-brand shadow-[0_0_0_6px_var(--brand-tint)]",
              status === "unknown" && "border-border bg-card border-2",
              selected && "ring-brand ring-offset-background ring-2 ring-offset-2"
            )}
            style={{ width: size, height: size }}
          >
            {status === "completed" ? (
              <Check className="size-3.5 text-white" strokeWidth={3} />
            ) : (
              <span
                className={cn(
                  "font-mono text-[13px] font-semibold",
                  status === "current" ? "text-white" : "text-tertiary"
                )}
              >
                {week.week_number}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

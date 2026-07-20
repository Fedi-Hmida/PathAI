import {
  ArrowLeftRight,
  CheckCircle2,
  Clock,
  Dumbbell,
  GitFork,
  Link as LinkIcon,
  Plus,
  TrendingDown,
  type LucideIcon,
} from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { formatConceptLabel } from "@/lib/utils";
import type { CurriculumChangeDTO, CurriculumChangeType } from "@/lib/types/adaptation";

const CHANGE_TYPE_ICON: Record<CurriculumChangeType, LucideIcon> = {
  insert_topic: Plus,
  add_practice_exercise: Dumbbell,
  reorder_topic: ArrowLeftRight,
  reduce_difficulty: TrendingDown,
  add_resource: LinkIcon,
  add_review_quiz: CheckCircle2,
  split_topic: GitFork,
  defer_topic: Clock,
};

export interface ChangeCardProps {
  change: CurriculumChangeDTO;
}

export function ChangeCard({ change }: ChangeCardProps) {
  const Icon = CHANGE_TYPE_ICON[change.change_type];

  return (
    <Card>
      <CardContent className="flex flex-col gap-3.5">
        <div className="flex flex-wrap items-center gap-3">
          <div className="bg-brand-tint flex size-8 flex-none items-center justify-center rounded-lg">
            <Icon className="text-brand size-4" />
          </div>
          <span className="text-foreground font-semibold">{formatConceptLabel(change.change_type)}</span>
          {change.target_week !== null ? (
            <span className="bg-surface-sunken text-muted-foreground rounded-md px-2 py-0.5 font-mono text-[11px]">
              Week {change.target_week}
            </span>
          ) : null}
          {change.topic_title ? (
            <span className="font-goal text-muted-foreground ml-auto text-right text-sm italic">
              {change.topic_title}
            </span>
          ) : null}
        </div>
        <p className="text-foreground text-[15px] leading-relaxed">{change.reason}</p>
        {change.affected_concept_ids.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {change.affected_concept_ids.map((conceptId) => (
              <span
                key={conceptId}
                className="bg-surface-sunken text-tertiary rounded-full px-2.5 py-1 text-xs"
              >
                {formatConceptLabel(conceptId)}
              </span>
            ))}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

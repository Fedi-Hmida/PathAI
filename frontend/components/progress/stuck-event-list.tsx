import { Flag } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { formatConceptLabel } from "@/lib/utils";
import type { StuckEventDTO } from "@/lib/types/progress";

export interface StuckEventListProps {
  events: StuckEventDTO[];
  topicTitleById: Map<string, string>;
}

export function StuckEventList({ events, topicTitleById }: StuckEventListProps) {
  if (events.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardContent className="flex flex-col gap-1">
        <h2 className="text-foreground mb-2.5 text-lg font-semibold">Where you&apos;ve gotten stuck</h2>
        {events.map((event, index) => (
          <div
            key={`${event.topic_id}-${event.created_at}-${index}`}
            className="border-border flex flex-col gap-2 border-t py-3.5 first:border-t-0 first:pt-0"
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <span className="text-foreground min-w-0 flex-1 text-[15px] font-semibold">
                {topicTitleById.get(event.topic_id) ?? event.topic_id}
              </span>
              <span className="text-warning inline-flex flex-none items-center gap-1.5 text-xs font-semibold whitespace-nowrap">
                <Flag className="size-3" fill="currentColor" strokeWidth={0} />
                Stuck · {new Date(event.created_at).toLocaleDateString()}
              </span>
            </div>
            {event.concept_ids.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {event.concept_ids.map((conceptId) => (
                  <span
                    key={conceptId}
                    className="bg-warning-tint text-warning rounded-full px-2.5 py-1 text-xs font-medium"
                  >
                    {formatConceptLabel(conceptId)}
                  </span>
                ))}
              </div>
            ) : null}
            <p className="text-muted-foreground text-[13px] leading-relaxed">{event.reason}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

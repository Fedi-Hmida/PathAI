import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { AdaptationEventDTO, AdaptationTriggerType } from "@/lib/types/adaptation";

const TRIGGER_LABEL: Record<AdaptationTriggerType, string> = {
  quiz_score_below_threshold: "After a Quiz",
  stuck_event_threshold: "After Getting Stuck",
  critic_score_below_threshold: "After a Curriculum Review",
};

export interface TriggerCardProps {
  event: AdaptationEventDTO;
}

export function TriggerCard({ event }: TriggerCardProps) {
  return (
    <Card>
      <CardContent>
        <div className="text-tertiary mb-2.5 text-[11px] font-semibold tracking-wide uppercase">
          {TRIGGER_LABEL[event.trigger_type]}
        </div>
        <TriggerBody event={event} />
      </CardContent>
    </Card>
  );
}

function TriggerBody({ event }: { event: AdaptationEventDTO }) {
  if (event.trigger_type === "quiz_score_below_threshold") {
    const scoreRaw = event.trigger_details.quiz_score;
    const thresholdRaw = event.trigger_details.threshold;
    const score = scoreRaw !== undefined ? Number.parseFloat(scoreRaw) : null;
    const threshold = thresholdRaw !== undefined ? Number.parseFloat(thresholdRaw) : null;

    if (score !== null && !Number.isNaN(score) && threshold !== null && !Number.isNaN(threshold)) {
      const tone = score < threshold ? "text-warning" : "text-success";
      return (
        <p className="text-foreground text-base leading-relaxed">
          Triggered by a quiz score of{" "}
          <strong className={cn("font-mono font-semibold", tone)}>{score.toFixed(2)}</strong> against
          a {threshold.toFixed(2)} threshold.
        </p>
      );
    }

    return (
      <p className="text-foreground text-base leading-relaxed">
        Triggered by a quiz score below the adaptation threshold.
      </p>
    );
  }

  if (event.trigger_type === "stuck_event_threshold") {
    const count = event.stuck_event_ids.length;
    return (
      <p className="text-foreground text-base leading-relaxed">
        Triggered by {count} stuck event{count === 1 ? "" : "s"}.
      </p>
    );
  }

  return (
    <p className="text-foreground text-base leading-relaxed">
      Triggered by a curriculum review score below the adaptation threshold.
    </p>
  );
}

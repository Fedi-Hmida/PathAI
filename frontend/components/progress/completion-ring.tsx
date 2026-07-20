import { ProgressRing } from "@/components/dashboard/progress-ring";
import { scoreBand } from "@/lib/score-band";

const TONE_COLOR: Record<ReturnType<typeof scoreBand>, string> = {
  success: "var(--success)",
  brand: "var(--brand)",
  warning: "var(--warning)",
};

export interface CompletionRingProps {
  value: number;
}

export function CompletionRing({ value }: CompletionRingProps) {
  return (
    <ProgressRing
      value={Math.round(value * 100)}
      size={200}
      strokeWidth={14}
      label="complete"
      indicatorColor={TONE_COLOR[scoreBand(value)]}
    />
  );
}

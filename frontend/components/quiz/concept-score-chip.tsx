import { scoreBand } from "@/lib/score-band";
import { formatConceptLabel } from "@/lib/utils";

export const CONCEPT_TONE_COLOR: Record<ReturnType<typeof scoreBand>, string> = {
  success: "var(--success)",
  brand: "var(--brand)",
  warning: "var(--warning)",
};

export const CONCEPT_TONE_TINT_CLASS: Record<ReturnType<typeof scoreBand>, string> = {
  success: "bg-success-tint",
  brand: "bg-brand-tint",
  warning: "bg-warning-tint",
};

const SIZE = 44;
const RADIUS = 17;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export interface ConceptScoreChipProps {
  conceptId: string;
  score: number;
  weak: boolean;
}

export function ConceptScoreChip({ conceptId, score, weak }: ConceptScoreChipProps) {
  const color = CONCEPT_TONE_COLOR[scoreBand(score)];
  const dashoffset = CIRCUMFERENCE - score * CIRCUMFERENCE;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: SIZE, height: SIZE }}>
        <svg width={SIZE} height={SIZE} style={{ transform: "rotate(-90deg)" }}>
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            fill="none"
            stroke="var(--surface-sunken)"
            strokeWidth={4}
          />
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            fill="none"
            stroke={color}
            strokeWidth={4}
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={dashoffset}
          />
        </svg>
        <div
          className="absolute inset-0 flex items-center justify-center font-mono text-xs font-medium"
          style={{ color }}
        >
          {Math.round(score * 100)}
        </div>
        {weak ? (
          <span className="bg-warning border-card absolute -top-0.5 -right-0.5 size-2.5 rounded-full border-2" />
        ) : null}
      </div>
      <span className="text-muted-foreground max-w-[88px] text-center text-xs leading-snug">
        {formatConceptLabel(conceptId)}
      </span>
    </div>
  );
}

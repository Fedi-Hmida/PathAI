import { AlertTriangle } from "lucide-react";

import { scoreBand } from "@/lib/score-band";
import { cn } from "@/lib/utils";

const TONE_BORDER: Record<ReturnType<typeof scoreBand>, string> = {
  success: "border-success text-success",
  brand: "border-brand text-brand",
  warning: "border-warning text-warning",
};

export interface QuizScoreStampProps {
  totalScore: number;
  correctCount: number;
  totalQuestions: number;
  feedback: string | null;
  adaptationTriggered: boolean;
}

export function QuizScoreStamp({
  totalScore,
  correctCount,
  totalQuestions,
  feedback,
  adaptationTriggered,
}: QuizScoreStampProps) {
  const tone = scoreBand(totalScore);

  return (
    <div className="flex flex-col items-center gap-4">
      {adaptationTriggered ? (
        <div className="bg-warning-tint border-warning text-foreground flex w-full max-w-lg items-center gap-2.5 rounded-xl border px-4 py-3.5">
          <AlertTriangle className="text-warning size-4 flex-none" />
          <span className="text-sm">This score is low enough to adjust your plan.</span>
        </div>
      ) : null}

      <div
        className={cn(
          "bg-card flex size-44 -rotate-3 items-center justify-center rounded-2xl border-4 shadow-md",
          TONE_BORDER[tone]
        )}
      >
        <span className="font-mono text-5xl font-semibold tabular-nums">
          {Math.round(totalScore * 100)}%
        </span>
      </div>

      <p className="text-muted-foreground font-mono text-sm">
        {correctCount} of {totalQuestions}
      </p>
      {feedback ? (
        <p className="text-muted-foreground max-w-md text-center text-base leading-relaxed">
          {feedback}
        </p>
      ) : null}
    </div>
  );
}

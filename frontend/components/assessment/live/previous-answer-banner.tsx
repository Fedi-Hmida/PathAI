import { AlertTriangle, CheckCircle2 } from "lucide-react";

import { cn } from "@/lib/utils";
import type { AssessmentAnswerDTO } from "@/lib/types/assessment";

function scoreTone(score: number): { bg: string; border: string; text: string; strong: boolean } {
  if (score >= 0.7) return { bg: "bg-success-tint", border: "border-success", text: "text-success", strong: true };
  if (score >= 0.4) return { bg: "bg-warning-tint", border: "border-warning", text: "text-warning", strong: false };
  return { bg: "bg-danger-tint", border: "border-danger", text: "text-danger", strong: false };
}

type PreviousAnswerBannerProps = {
  answer: AssessmentAnswerDTO;
};

export function PreviousAnswerBanner({ answer }: PreviousAnswerBannerProps) {
  const tone = scoreTone(answer.score);
  const Icon = tone.strong ? CheckCircle2 : AlertTriangle;

  return (
    <div className={cn("flex items-start gap-2.5 rounded-md border px-5 py-4", tone.bg, tone.border)}>
      <Icon className={cn("mt-0.5 size-[18px] flex-none", tone.text)} />
      <div>
        <div className={cn("text-sm font-semibold", tone.text)}>
          {tone.strong ? "Correct — nice" : "Not quite"}
        </div>
        {answer.feedback ? (
          <div className="text-muted-foreground mt-0.5 text-sm">{answer.feedback}</div>
        ) : null}
      </div>
    </div>
  );
}

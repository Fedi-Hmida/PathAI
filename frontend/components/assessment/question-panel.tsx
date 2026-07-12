import { ArrowLeft, ArrowRight, Check } from "lucide-react";

import { cn, formatConceptLabel } from "@/lib/utils";
import type { AssessmentAnswerDTO, DifficultyLevel } from "@/lib/types/assessment";

const DIFFICULTY_CONFIG: Record<DifficultyLevel, { label: string; className: string }> = {
  beginner: { label: "Beginner", className: "bg-surface-sunken text-tertiary" },
  intermediate: { label: "Intermediate", className: "bg-brand-tint text-brand" },
  advanced: { label: "Advanced", className: "bg-warning-tint text-warning" },
};

function scoreTone(score: number): { text: string; bg: string } {
  if (score >= 0.7) return { text: "text-success", bg: "bg-success-tint" };
  if (score >= 0.4) return { text: "text-warning", bg: "bg-warning-tint" };
  return { text: "text-danger", bg: "bg-danger-tint" };
}

type QuestionPanelProps = {
  answer: AssessmentAnswerDTO;
  index: number;
  totalCount: number;
  onNavigate: (index: number) => void;
};

export function QuestionPanel({ answer, index, totalCount, onNavigate }: QuestionPanelProps) {
  const { question } = answer;
  const difficulty = DIFFICULTY_CONFIG[question.difficulty];
  const tone = scoreTone(answer.score);
  const selectedOptions = new Set(answer.selected_options);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-tertiary font-mono text-[13px] font-semibold">
            Question {index + 1} of {totalCount}
          </span>
          <span className={cn("rounded-full px-2.5 py-0.5 text-[11px] font-semibold", difficulty.className)}>
            {difficulty.label}
          </span>
          <span className={cn("rounded-full px-2.5 py-0.5 text-[11px] font-semibold", tone.bg, tone.text)}>
            {Math.round(answer.score * 100)}% score
          </span>
        </div>
        <h1 className="font-goal text-foreground mt-2 text-[26px] leading-tight font-medium">
          {question.prompt}
        </h1>
      </div>

      {question.options.length > 0 ? (
        <div className="flex flex-col gap-2.5">
          {question.options.map((option) => {
            const selected = selectedOptions.has(option);
            return (
              <div
                key={option}
                className={cn(
                  "flex items-center gap-3 rounded-xl border px-4 py-3 text-[14px]",
                  selected ? "border-brand bg-brand-tint text-foreground" : "border-border text-muted-foreground"
                )}
              >
                <span
                  className={cn(
                    "flex size-5 flex-none items-center justify-center rounded-full border",
                    selected ? "border-brand bg-brand" : "border-border"
                  )}
                >
                  {selected ? <Check className="size-3 text-white" strokeWidth={3} /> : null}
                </span>
                {option}
              </div>
            );
          })}
        </div>
      ) : null}

      {answer.answer_text ? (
        <div className="border-border bg-surface-sunken rounded-xl border px-4 py-3.5">
          <div className="text-tertiary mb-1 text-[11px] font-bold tracking-wide uppercase">
            Learner answer
          </div>
          <p className="text-foreground text-[14px] leading-relaxed italic">
            &ldquo;{answer.answer_text}&rdquo;
          </p>
        </div>
      ) : null}

      {answer.feedback ? (
        <div className={cn("flex items-start gap-3 rounded-xl px-4 py-3.5", tone.bg)}>
          <div>
            <div className={cn("mb-1 text-[11px] font-bold tracking-wide uppercase", tone.text)}>
              Feedback
            </div>
            <div className="text-foreground text-[13px] leading-relaxed">{answer.feedback}</div>
          </div>
        </div>
      ) : null}

      {answer.concept_scores.length > 0 ? (
        <div className="flex flex-wrap gap-2.5">
          {answer.concept_scores.map((update) => (
            <span
              key={update.concept_id}
              className="bg-surface-sunken text-muted-foreground inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium"
            >
              {formatConceptLabel(update.concept_id)}
              <span
                className={cn(
                  "font-tabular font-mono",
                  update.score_delta >= 0 ? "text-success" : "text-danger"
                )}
              >
                {update.score_delta >= 0 ? "+" : ""}
                {update.score_delta.toFixed(2)}
              </span>
            </span>
          ))}
        </div>
      ) : null}

      <div className="border-border flex items-center justify-between gap-5 border-t pt-5">
        {index > 0 ? (
          <button
            type="button"
            onClick={() => onNavigate(index - 1)}
            className="text-muted-foreground hover:text-brand inline-flex items-center gap-1.5 text-left text-[13px]"
          >
            <ArrowLeft className="size-3.5 flex-none" />
            Question {index}
          </button>
        ) : (
          <span />
        )}
        {index < totalCount - 1 ? (
          <button
            type="button"
            onClick={() => onNavigate(index + 1)}
            className="text-muted-foreground hover:text-brand inline-flex items-center gap-1.5 text-right text-[13px]"
          >
            Question {index + 2}
            <ArrowRight className="size-3.5 flex-none" />
          </button>
        ) : (
          <span />
        )}
      </div>
    </div>
  );
}

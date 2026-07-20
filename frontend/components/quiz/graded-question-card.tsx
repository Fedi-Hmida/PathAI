import { Check, X } from "lucide-react";

import { CONCEPT_TONE_COLOR, CONCEPT_TONE_TINT_CLASS } from "@/components/quiz/concept-score-chip";
import { correlateOptions, wasAnsweredCorrectly } from "@/components/quiz/option-correlation";
import { Card, CardContent } from "@/components/ui/card";
import { scoreBand } from "@/lib/score-band";
import { cn, formatConceptLabel } from "@/lib/utils";
import type { DifficultyLevel } from "@/lib/types/curriculum";
import type { ConceptQuizScore, QuizAnswerSubmission, QuizQuestionDTO } from "@/lib/types/quiz";

const DIFFICULTY_CONFIG: Record<DifficultyLevel, { label: string; className: string }> = {
  beginner: { label: "Beginner", className: "bg-surface-sunken text-tertiary" },
  intermediate: { label: "Intermediate", className: "bg-brand-tint text-brand" },
  advanced: { label: "Advanced", className: "bg-warning-tint text-warning" },
};

export interface GradedQuestionCardProps {
  question: QuizQuestionDTO;
  answer: QuizAnswerSubmission | undefined;
  conceptScoresByConceptId: Map<string, ConceptQuizScore>;
}

export function GradedQuestionCard({
  question,
  answer,
  conceptScoresByConceptId,
}: GradedQuestionCardProps) {
  const options = correlateOptions(question, answer);
  const isCorrect = wasAnsweredCorrectly(question, answer);
  const difficulty = DIFFICULTY_CONFIG[question.difficulty];

  return (
    <Card>
      <CardContent className="flex flex-col gap-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <span
              className={cn(
                "mt-0.5 flex size-7 flex-none items-center justify-center rounded-full",
                isCorrect ? "bg-success" : "bg-warning"
              )}
            >
              {isCorrect ? (
                <Check className="text-primary-foreground size-3.5" />
              ) : (
                <X className="text-primary-foreground size-3.5" />
              )}
            </span>
            <p className="text-foreground pt-0.5 text-[15px] leading-snug font-semibold">
              {question.prompt}
            </p>
          </div>
          <div className="flex flex-none flex-col items-end gap-2">
            <span
              className={cn(
                "rounded-full px-2.5 py-1 text-[11px] font-semibold whitespace-nowrap",
                difficulty.className
              )}
            >
              {difficulty.label}
            </span>
            <span className="text-muted-foreground font-mono text-xs">
              {question.points} pt{question.points === 1 ? "" : "s"}
            </span>
          </div>
        </div>

        <div className="ml-10.5 flex flex-wrap gap-2">
          {options.map((option) => (
            <span
              key={option.label}
              className={cn(
                "rounded-full border px-3.5 py-1.5 text-sm",
                option.tone === "correct" &&
                  "border-success bg-success-tint text-success font-semibold",
                option.tone === "wrong" &&
                  "border-warning bg-warning-tint text-warning line-through",
                option.tone === "plain" && "border-border text-muted-foreground"
              )}
            >
              {option.tone === "wrong" ? "✕ " : null}
              {option.label}
            </span>
          ))}
        </div>

        {question.explanation ? (
          <p className="text-muted-foreground ml-10.5 max-w-2xl text-sm leading-relaxed">
            {question.explanation}
          </p>
        ) : null}

        <div className="ml-10.5 flex flex-wrap gap-2">
          {question.concept_ids.map((conceptId) => {
            const conceptScore = conceptScoresByConceptId.get(conceptId);
            return conceptScore ? (
              <ConceptChipMini
                key={conceptId}
                conceptId={conceptId}
                score={conceptScore.score}
              />
            ) : (
              <span
                key={conceptId}
                className="bg-surface-sunken text-tertiary rounded-full px-2.5 py-1 text-xs"
              >
                {formatConceptLabel(conceptId)}
              </span>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

const MINI_SIZE = 16;
const MINI_RADIUS = 6;
const MINI_CIRCUMFERENCE = 2 * Math.PI * MINI_RADIUS;

function ConceptChipMini({ conceptId, score }: { conceptId: string; score: number }) {
  const tone = scoreBand(score);
  const color = CONCEPT_TONE_COLOR[tone];
  const dashoffset = MINI_CIRCUMFERENCE - score * MINI_CIRCUMFERENCE;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full py-1 pr-2.5 pl-1 text-xs font-medium",
        CONCEPT_TONE_TINT_CLASS[tone]
      )}
      style={{ color }}
    >
      <svg width={MINI_SIZE} height={MINI_SIZE} style={{ transform: "rotate(-90deg)" }}>
        <circle
          cx={MINI_SIZE / 2}
          cy={MINI_SIZE / 2}
          r={MINI_RADIUS}
          fill="none"
          stroke="var(--surface-sunken)"
          strokeWidth={2.5}
        />
        <circle
          cx={MINI_SIZE / 2}
          cy={MINI_SIZE / 2}
          r={MINI_RADIUS}
          fill="none"
          stroke={color}
          strokeWidth={2.5}
          strokeLinecap="round"
          strokeDasharray={MINI_CIRCUMFERENCE}
          strokeDashoffset={dashoffset}
        />
      </svg>
      {formatConceptLabel(conceptId)}
    </span>
  );
}

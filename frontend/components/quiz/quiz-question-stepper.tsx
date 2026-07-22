import { QuizOptionList } from "@/components/quiz/quiz-option-list";
import { QuizProgressDots } from "@/components/quiz/quiz-progress-dots";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { DifficultyLevel } from "@/lib/types/curriculum";
import type { LearnerQuizQuestionDTO } from "@/lib/types/quiz";

const DIFFICULTY_CONFIG: Record<DifficultyLevel, { label: string; className: string }> = {
  beginner: { label: "Beginner", className: "bg-surface-sunken text-tertiary" },
  intermediate: { label: "Intermediate", className: "bg-brand-tint text-brand" },
  advanced: { label: "Advanced", className: "bg-warning-tint text-warning" },
};

export interface QuizQuestionStepperProps {
  question: LearnerQuizQuestionDTO;
  index: number;
  total: number;
  answeredIndexes: ReadonlySet<number>;
  selected: string | null;
  onSelect: (option: string) => void;
  onPrevious: () => void;
  onNext: () => void;
  onSubmit: () => void;
  isFirst: boolean;
  isLast: boolean;
  submitting: boolean;
  submitError: string | null;
}

export function QuizQuestionStepper({
  question,
  index,
  total,
  answeredIndexes,
  selected,
  onSelect,
  onPrevious,
  onNext,
  onSubmit,
  isFirst,
  isLast,
  submitting,
  submitError,
}: QuizQuestionStepperProps) {
  const difficulty = DIFFICULTY_CONFIG[question.difficulty];

  return (
    <div className="flex flex-col gap-6">
      <QuizProgressDots total={total} currentIndex={index} answeredIndexes={answeredIndexes} />

      <Card>
        <CardContent className="flex flex-col gap-5">
          <div className="flex items-start justify-between gap-4">
            <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
              Question {index + 1} of {total}
            </span>
            <span
              className={cn(
                "rounded-full px-2.5 py-1 text-[11px] font-semibold whitespace-nowrap",
                difficulty.className
              )}
            >
              {difficulty.label}
            </span>
          </div>

          <p className="text-foreground text-lg leading-snug font-semibold">{question.prompt}</p>

          <QuizOptionList options={question.options} selected={selected} onSelect={onSelect} />
        </CardContent>
      </Card>

      {submitError ? (
        <p className="text-danger text-center text-sm">{submitError}</p>
      ) : null}

      <div className="flex items-center justify-between gap-3">
        <Button variant="outline" onClick={onPrevious} disabled={isFirst || submitting}>
          Previous
        </Button>
        {isLast ? (
          <Button onClick={onSubmit} disabled={selected === null || submitting}>
            {submitting ? "Submitting…" : "Submit Quiz"}
          </Button>
        ) : (
          <Button onClick={onNext} disabled={selected === null}>
            Next Question
          </Button>
        )}
      </div>
    </div>
  );
}

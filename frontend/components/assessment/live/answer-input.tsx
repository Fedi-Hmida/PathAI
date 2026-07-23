import { Check } from "lucide-react";

import { SelfRatingScale } from "@/components/assessment/live/self-rating-scale";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import type { AssessmentQuestionDTO } from "@/lib/types/assessment";

type AnswerInputProps = {
  question: AssessmentQuestionDTO;
  disabled: boolean;
  selectedOption: string | null;
  onSelectOption: (option: string) => void;
  textAnswer: string;
  onTextAnswerChange: (value: string) => void;
  selfRating: number | null;
  onSelfRatingChange: (value: number) => void;
};

export function AnswerInput({
  question,
  disabled,
  selectedOption,
  onSelectOption,
  textAnswer,
  onTextAnswerChange,
  selfRating,
  onSelfRatingChange,
}: AnswerInputProps) {
  if (question.question_type === "multiple_choice") {
    return (
      <div className="flex flex-col gap-2.5">
        {question.options.map((option, index) => {
          const selected = selectedOption === option;
          return (
            <button
              key={option}
              type="button"
              data-testid="assessment-option"
              disabled={disabled}
              onClick={() => onSelectOption(option)}
              className={cn(
                "flex w-full items-center gap-3 rounded-xl border px-4 py-3 text-left text-[14px] transition-colors",
                selected
                  ? "border-brand bg-brand-tint text-foreground"
                  : "border-border text-foreground hover:border-brand-border",
                disabled && "cursor-default"
              )}
            >
              <span
                className={cn(
                  "flex size-5 flex-none items-center justify-center rounded-full border text-[11px] font-semibold",
                  selected ? "border-brand bg-brand text-white" : "border-border text-tertiary"
                )}
              >
                {selected ? <Check className="size-3" strokeWidth={3} /> : String.fromCharCode(65 + index)}
              </span>
              {option}
            </button>
          );
        })}
      </div>
    );
  }

  if (question.question_type === "self_rating") {
    return <SelfRatingScale value={selfRating} onChange={onSelfRatingChange} disabled={disabled} />;
  }

  return (
    <Textarea
      value={textAnswer}
      onChange={(event) => onTextAnswerChange(event.target.value)}
      disabled={disabled}
      placeholder="Type your answer..."
      maxLength={1200}
      rows={4}
    />
  );
}

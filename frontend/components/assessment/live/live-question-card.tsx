"use client";

import * as React from "react";

import { AnswerInput } from "@/components/assessment/live/answer-input";
import { SelfRatingScale } from "@/components/assessment/live/self-rating-scale";
import { Button } from "@/components/ui/button";
import { formatConceptLabel } from "@/lib/utils";
import type { AssessmentAnswerCreate, AssessmentQuestionDTO } from "@/lib/types/assessment";

type LiveQuestionCardProps = {
  question: AssessmentQuestionDTO;
  questionNumber: number;
  submitting: boolean;
  onSubmit: (payload: AssessmentAnswerCreate) => void;
};

export function LiveQuestionCard({
  question,
  questionNumber,
  submitting,
  onSubmit,
}: LiveQuestionCardProps) {
  const [selectedOption, setSelectedOption] = React.useState<string | null>(null);
  const [textAnswer, setTextAnswer] = React.useState("");
  const [selfRating, setSelfRating] = React.useState<number | null>(null);

  const hasPrimaryAnswer =
    question.question_type === "multiple_choice"
      ? selectedOption !== null
      : question.question_type === "self_rating"
        ? selfRating !== null
        : textAnswer.trim().length > 0;

  function handleSubmit() {
    if (!hasPrimaryAnswer || submitting) {
      return;
    }
    const payload: AssessmentAnswerCreate = { question_id: question.question_id };
    if (question.question_type === "multiple_choice" && selectedOption !== null) {
      payload.selected_options = [selectedOption];
    }
    if (question.question_type === "short_answer") {
      payload.answer_text = textAnswer.trim();
    }
    if (selfRating !== null) {
      payload.self_rating = selfRating;
    }
    onSubmit(payload);
  }

  return (
    <div className="border-border bg-card rounded-2xl border p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-3">
        <span className="bg-warning-tint text-warning inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold">
          {formatConceptLabel(question.target_concepts[0] ?? "")} · {question.difficulty}
        </span>
        <span className="text-tertiary font-mono text-[11px]">Q{questionNumber}</span>
      </div>

      <div className="font-goal text-foreground mb-5 text-[19px] leading-snug font-medium">
        {question.prompt}
      </div>

      <div className="mb-6">
        <AnswerInput
          question={question}
          disabled={submitting}
          selectedOption={selectedOption}
          onSelectOption={setSelectedOption}
          textAnswer={textAnswer}
          onTextAnswerChange={setTextAnswer}
          selfRating={selfRating}
          onSelfRatingChange={setSelfRating}
        />
      </div>

      <div className="border-border flex flex-wrap items-center justify-between gap-5 border-t pt-5">
        {question.question_type === "self_rating" ? (
          <span />
        ) : (
          <div>
            <div className="text-foreground mb-2 text-sm font-medium">How confident are you?</div>
            <SelfRatingScale value={selfRating} onChange={setSelfRating} disabled={submitting} />
          </div>
        )}

        <Button onClick={handleSubmit} disabled={!hasPrimaryAnswer || submitting}>
          {submitting ? "Submitting..." : "Submit"}
        </Button>
      </div>
    </div>
  );
}

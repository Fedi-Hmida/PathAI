"use client";

import { Check } from "lucide-react";

import { type TrailStone, type TrailStoneStatus, WavyTrail } from "@/components/ui/wavy-trail";
import { cn } from "@/lib/utils";
import type { AssessmentAnswerDTO } from "@/lib/types/assessment";

const STONE_SIZE = 32;

type QuestionTrailProps = {
  answers: AssessmentAnswerDTO[];
  questionCount: number;
  selectedIndex: number;
  onSelectIndex: (index: number) => void;
};

export function QuestionTrail({
  answers,
  questionCount,
  selectedIndex,
  onSelectIndex,
}: QuestionTrailProps) {
  const totalStones = Math.max(questionCount, answers.length);

  const stones: TrailStone[] = Array.from({ length: totalStones }, (_, index) => {
    const answer = answers[index] ?? null;
    const selected = index === selectedIndex;
    const status: TrailStoneStatus =
      answer === null ? "unknown" : selected ? "current" : "completed";

    return {
      key: String(index),
      status,
      size: STONE_SIZE,
      selected,
      disabled: answer === null,
      title:
        answer === null
          ? `Question ${index + 1}: not yet answered`
          : `Question ${index + 1}: ${answer.question.prompt}`,
      onClick: answer === null ? undefined : () => onSelectIndex(index),
      content:
        status === "completed" ? (
          <Check className="size-4 text-white" strokeWidth={3} />
        ) : (
          <span
            className={cn(
              "font-mono text-base font-semibold",
              status === "current" ? "text-white" : "text-tertiary"
            )}
          >
            {index + 1}
          </span>
        ),
    };
  });

  return <WavyTrail stones={stones} />;
}

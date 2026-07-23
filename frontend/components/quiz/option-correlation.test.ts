import { describe, expect, it } from "vitest";

import {
  correlateOptions,
  findAnswerForQuestion,
  wasAnsweredCorrectly,
} from "@/components/quiz/option-correlation";
import type { QuizAnswerSubmission, QuizQuestionDTO } from "@/lib/types/quiz";

function question(overrides: Partial<QuizQuestionDTO> = {}): QuizQuestionDTO {
  return {
    question_id: "question_1",
    question_type: "multiple_choice",
    prompt: "Which option is correct?",
    concept_ids: [],
    difficulty: "beginner",
    correct_answer: "Right answer",
    points: 1,
    options: ["Right answer", "Wrong answer A", "Wrong answer B"],
    rubric: null,
    explanation: null,
    ...overrides,
  };
}

function answer(selected: string | null): QuizAnswerSubmission | undefined {
  if (selected === null) {
    return undefined;
  }
  return { question_id: "question_1", answer_text: null, selected_options: [selected] };
}

describe("findAnswerForQuestion", () => {
  it("finds the submission matching the question id", () => {
    const answers: QuizAnswerSubmission[] = [
      { question_id: "q1", answer_text: null, selected_options: ["x"] },
      { question_id: "q2", answer_text: null, selected_options: ["y"] },
    ];
    expect(findAnswerForQuestion(answers, "q2")).toEqual(answers[1]);
    expect(findAnswerForQuestion(answers, "q_missing")).toBeUndefined();
  });
});

describe("wasAnsweredCorrectly", () => {
  it("is true only when the selected option exactly matches correct_answer", () => {
    expect(wasAnsweredCorrectly(question(), answer("Right answer"))).toBe(true);
    expect(wasAnsweredCorrectly(question(), answer("Wrong answer A"))).toBe(false);
  });

  it("is false when there is no answer at all", () => {
    expect(wasAnsweredCorrectly(question(), undefined)).toBe(false);
  });
});

describe("correlateOptions", () => {
  it("marks the correct option 'correct' even when the learner picked it", () => {
    const views = correlateOptions(question(), answer("Right answer"));
    const correctView = views.find((view) => view.label === "Right answer")!;
    expect(correctView.tone).toBe("correct");
    // Every other option is plain, not wrong, once the learner got it right.
    expect(views.filter((view) => view.tone === "wrong")).toHaveLength(0);
  });

  it("marks the correct answer 'correct' AND the learner's wrong pick 'wrong', everything else plain", () => {
    const views = correlateOptions(question(), answer("Wrong answer A"));
    const byLabel = new Map(views.map((view) => [view.label, view.tone]));
    expect(byLabel.get("Right answer")).toBe("correct");
    expect(byLabel.get("Wrong answer A")).toBe("wrong");
    expect(byLabel.get("Wrong answer B")).toBe("plain");
  });

  it("marks only the correct answer when the question was never answered (skipped)", () => {
    const views = correlateOptions(question(), undefined);
    const byLabel = new Map(views.map((view) => [view.label, view.tone]));
    expect(byLabel.get("Right answer")).toBe("correct");
    expect(byLabel.get("Wrong answer A")).toBe("plain");
    expect(byLabel.get("Wrong answer B")).toBe("plain");
  });
});

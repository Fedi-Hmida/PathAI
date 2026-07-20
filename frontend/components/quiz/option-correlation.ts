import type { QuizAnswerSubmission, QuizQuestionDTO } from "@/lib/types/quiz";

export type OptionTone = "correct" | "wrong" | "plain";

export type OptionView = {
  label: string;
  tone: OptionTone;
};

export function findAnswerForQuestion(
  answers: QuizAnswerSubmission[],
  questionId: string
): QuizAnswerSubmission | undefined {
  return answers.find((answer) => answer.question_id === questionId);
}

export function wasAnsweredCorrectly(
  question: QuizQuestionDTO,
  answer: QuizAnswerSubmission | undefined
): boolean {
  return answer?.selected_options[0] === question.correct_answer;
}

export function correlateOptions(
  question: QuizQuestionDTO,
  answer: QuizAnswerSubmission | undefined
): OptionView[] {
  const selected = answer?.selected_options[0];
  const wasCorrect = wasAnsweredCorrectly(question, answer);

  return question.options.map((option) => {
    if (option === question.correct_answer) {
      return { label: option, tone: "correct" };
    }
    if (!wasCorrect && option === selected) {
      return { label: option, tone: "wrong" };
    }
    return { label: option, tone: "plain" };
  });
}

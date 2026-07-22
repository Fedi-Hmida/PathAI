"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";

import { RequireAuth } from "@/components/auth/require-auth";
import { QuizQuestionStepper } from "@/components/quiz/quiz-question-stepper";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/client";
import { getLearnerQuiz, submitQuizAttempt } from "@/lib/api/quiz";
import type { LearnerQuizDTO } from "@/lib/types/quiz";

type QuizTakeLoadState =
  | { kind: "loading" }
  | { kind: "not_found" }
  | { kind: "invalid_id" }
  | { kind: "ready"; quiz: LearnerQuizDTO }
  | { kind: "error"; message: string };

export default function QuizTakePage() {
  return (
    <RequireAuth>
      <React.Suspense fallback={<QuizTakeSkeleton />}>
        <QuizTakeView />
      </React.Suspense>
    </RequireAuth>
  );
}

function QuizTakeView() {
  const params = useParams<{ quizId: string }>();
  const quizId = params.quizId;
  const router = useRouter();

  const [state, setState] = React.useState<QuizTakeLoadState>({ kind: "loading" });
  const [currentIndex, setCurrentIndex] = React.useState(0);
  const [answers, setAnswers] = React.useState<Record<string, string>>({});
  const [submitting, setSubmitting] = React.useState(false);
  const [submitError, setSubmitError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let cancelled = false;

    getLearnerQuiz(quizId)
      .then((quiz) => {
        if (!cancelled) {
          setState({ kind: "ready", quiz });
        }
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        if (error instanceof ApiError && error.status === 404) {
          setState({ kind: "not_found" });
          return;
        }
        // QuizId requires a "quiz_" prefix + pattern (schemas/ids.py); a
        // malformed id fails FastAPI's request validation with 422 before
        // reaching the not-found path.
        if (error instanceof ApiError && error.status === 422) {
          setState({ kind: "invalid_id" });
          return;
        }
        const message =
          error instanceof ApiError ? error.message : "Unable to reach the PathAI backend.";
        setState({ kind: "error", message });
      });

    return () => {
      cancelled = true;
    };
  }, [quizId]);

  const handleSubmit = React.useCallback(
    (quiz: LearnerQuizDTO) => {
      setSubmitting(true);
      setSubmitError(null);
      const submission = quiz.questions.map((question) => ({
        question_id: question.question_id,
        answer_text: null,
        selected_options: answers[question.question_id] ? [answers[question.question_id]!] : [],
      }));
      submitQuizAttempt(quizId, submission)
        .then((review) => {
          router.replace(`/quiz/${quizId}/attempts/${review.attempt.quiz_attempt_id}`);
        })
        .catch((error: unknown) => {
          setSubmitting(false);
          const message =
            error instanceof ApiError ? error.message : "Unable to reach the PathAI backend.";
          setSubmitError(message);
        });
    },
    [answers, quizId, router]
  );

  if (state.kind === "loading") {
    return <QuizTakeSkeleton />;
  }

  if (state.kind === "error") {
    return (
      <Alert variant="destructive">
        <AlertTitle>Couldn&apos;t load this quiz</AlertTitle>
        <AlertDescription>{state.message}</AlertDescription>
      </Alert>
    );
  }

  if (state.kind === "invalid_id") {
    return <p className="text-muted-foreground text-sm">That doesn&apos;t look like a valid quiz ID.</p>;
  }

  if (state.kind === "not_found") {
    return <p className="text-muted-foreground text-sm">Quiz not found.</p>;
  }

  const { quiz } = state;
  const question = quiz.questions[currentIndex]!;
  const answeredIndexes = new Set(
    quiz.questions.reduce<number[]>((indexes, candidate, index) => {
      if (answers[candidate.question_id]) {
        indexes.push(index);
      }
      return indexes;
    }, [])
  );

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-8">
      <div>
        <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">Quiz</span>
        <h1 className="font-goal text-foreground mt-0.5 text-2xl leading-tight font-medium italic">
          {quiz.title}
        </h1>
      </div>

      <QuizQuestionStepper
        question={question}
        index={currentIndex}
        total={quiz.questions.length}
        answeredIndexes={answeredIndexes}
        selected={answers[question.question_id] ?? null}
        onSelect={(option) =>
          setAnswers((previous) => ({ ...previous, [question.question_id]: option }))
        }
        onPrevious={() => setCurrentIndex((index) => Math.max(0, index - 1))}
        onNext={() =>
          setCurrentIndex((index) => Math.min(quiz.questions.length - 1, index + 1))
        }
        onSubmit={() => handleSubmit(quiz)}
        isFirst={currentIndex === 0}
        isLast={currentIndex === quiz.questions.length - 1}
        submitting={submitting}
        submitError={submitError}
      />
    </div>
  );
}

function QuizTakeSkeleton() {
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-8">
      <div className="flex flex-col gap-2.5">
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-8 w-64" />
      </div>
      <div className="flex justify-center gap-2">
        {Array.from({ length: 5 }).map((_, index) => (
          <Skeleton key={index} className="size-2.5 rounded-full" />
        ))}
      </div>
      <Skeleton className="h-64 w-full rounded-xl" />
      <div className="flex justify-between">
        <Skeleton className="h-9 w-24 rounded-md" />
        <Skeleton className="h-9 w-32 rounded-md" />
      </div>
    </div>
  );
}

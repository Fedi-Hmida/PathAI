"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { RequireAuth } from "@/components/auth/require-auth";
import { ConceptScoreChip } from "@/components/quiz/concept-score-chip";
import { GradedQuestionCard } from "@/components/quiz/graded-question-card";
import { findAnswerForQuestion } from "@/components/quiz/option-correlation";
import { QuizScoreStamp } from "@/components/quiz/quiz-score-stamp";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/client";
import { getQuizAttemptReview } from "@/lib/api/quiz";
import { isScoredQuizAttemptReview } from "@/lib/types/quiz";
import type { QuizAttemptReviewDTO } from "@/lib/types/quiz";

type QuizReviewLoadState =
  | { kind: "loading" }
  | { kind: "not_found" }
  | { kind: "invalid_id" }
  | { kind: "ready"; review: QuizAttemptReviewDTO }
  | { kind: "error"; message: string };

export default function QuizAttemptReviewPage() {
  return (
    <RequireAuth>
      <React.Suspense fallback={<QuizReviewSkeleton />}>
        <QuizAttemptReviewView />
      </React.Suspense>
    </RequireAuth>
  );
}

function QuizAttemptReviewView() {
  const params = useParams<{ quizId: string; attemptId: string }>();
  const { quizId, attemptId } = params;

  const [state, setState] = React.useState<QuizReviewLoadState>({ kind: "loading" });

  React.useEffect(() => {
    let cancelled = false;

    getQuizAttemptReview(quizId, attemptId)
      .then((review) => {
        if (!cancelled) {
          setState({ kind: "ready", review });
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
        // QuizId/AttemptId both require a prefix + pattern (schemas/ids.py);
        // a malformed id fails FastAPI's request validation with 422 before
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
  }, [quizId, attemptId]);

  if (state.kind === "loading") {
    return <QuizReviewSkeleton />;
  }

  if (state.kind === "error") {
    return (
      <Alert variant="destructive">
        <AlertTitle>Couldn&apos;t load this quiz result</AlertTitle>
        <AlertDescription>{state.message}</AlertDescription>
      </Alert>
    );
  }

  if (state.kind === "invalid_id") {
    return (
      <p className="text-muted-foreground text-sm">
        That doesn&apos;t look like a valid quiz result ID.
      </p>
    );
  }

  if (state.kind === "not_found") {
    return <p className="text-muted-foreground text-sm">Quiz attempt not found.</p>;
  }

  const { review } = state;
  const { attempt } = review;
  const conceptScoresByConceptId = new Map(
    attempt.concept_scores.map((entry) => [entry.concept_id, entry])
  );

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center gap-3">
        <Link
          href={`/curriculum/${attempt.curriculum_id}`}
          aria-label="Back to curriculum"
          className="border-border text-muted-foreground hover:bg-surface-sunken hover:text-foreground flex size-9 flex-none items-center justify-center rounded-full border"
        >
          <ArrowLeft className="size-4" />
        </Link>
        <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
          Quiz
        </span>
      </div>

      <div>
        <h1 className="font-goal text-foreground text-3xl leading-tight font-medium italic">
          Quiz Results
        </h1>
        <p className="text-tertiary mt-2.5 font-mono text-xs">
          Submitted {new Date(attempt.submitted_at).toLocaleString()}
        </p>
      </div>

      {isScoredQuizAttemptReview(review) ? (
        <>
          <QuizScoreStamp
            totalScore={attempt.total_score}
            correctCount={attempt.correct_count}
            totalQuestions={attempt.total_questions}
            feedback={attempt.feedback}
            adaptationTriggered={attempt.adaptation_triggered}
          />

          <div className="border-border flex flex-wrap justify-center gap-7 border-b pb-8">
            {attempt.concept_scores.map((entry) => (
              <ConceptScoreChip
                key={entry.concept_id}
                conceptId={entry.concept_id}
                score={entry.score}
                weak={attempt.weak_concepts.includes(entry.concept_id)}
              />
            ))}
          </div>

          <div className="flex flex-col gap-5">
            {review.questions.map((question) => (
              <GradedQuestionCard
                key={question.question_id}
                question={question}
                answer={findAnswerForQuestion(attempt.answers, question.question_id)}
                conceptScoresByConceptId={conceptScoresByConceptId}
              />
            ))}
          </div>
        </>
      ) : (
        <p className="text-muted-foreground text-sm">This attempt hasn&apos;t been scored yet.</p>
      )}

      <div className="border-border border-t pt-6 text-center">
        <Link
          href={`/curriculum/${attempt.curriculum_id}`}
          className="text-brand text-sm font-semibold hover:underline"
        >
          Review the full curriculum <span aria-hidden="true">→</span>
        </Link>
      </div>
    </div>
  );
}

function QuizReviewSkeleton() {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center gap-3">
        <Skeleton className="size-9 rounded-full" />
        <Skeleton className="h-3 w-16" />
      </div>
      <div className="flex flex-col gap-2.5">
        <Skeleton className="h-9 w-56" />
        <Skeleton className="h-3 w-48" />
      </div>
      <div className="flex flex-col items-center gap-4">
        <Skeleton className="size-44 rounded-2xl" />
        <Skeleton className="h-4 w-20" />
      </div>
      <div className="flex justify-center gap-7">
        <Skeleton className="size-11 rounded-full" />
        <Skeleton className="size-11 rounded-full" />
        <Skeleton className="size-11 rounded-full" />
      </div>
      <div className="flex flex-col gap-5">
        <Skeleton className="h-32 w-full rounded-xl" />
        <Skeleton className="h-32 w-full rounded-xl" />
      </div>
    </div>
  );
}

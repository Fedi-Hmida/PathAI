"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";

import { RequireAuth } from "@/components/auth/require-auth";
import { ConceptSidebar } from "@/components/assessment/live/concept-sidebar";
import { LiveAssessmentHeader } from "@/components/assessment/live/live-assessment-header";
import { LiveQuestionCard } from "@/components/assessment/live/live-question-card";
import { PreviousAnswerBanner } from "@/components/assessment/live/previous-answer-banner";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getAssessment, submitAssessmentAnswer } from "@/lib/api/assessment";
import { ApiError } from "@/lib/api/client";
import { getGoal } from "@/lib/api/goal";
import { generateMyWorkspace } from "@/lib/api/workspace";
import type {
  AssessmentAnswerCreate,
  AssessmentAnswerDTO,
  AssessmentSessionDTO,
} from "@/lib/types/assessment";

const TOTAL_QUESTIONS = 5;

type LoadState =
  | { kind: "loading" }
  | { kind: "invalid_id" }
  | { kind: "not_found" }
  | { kind: "error"; message: string }
  | { kind: "ready"; session: AssessmentSessionDTO; goalText: string; lastAnswer: AssessmentAnswerDTO | null };

type GenerationState =
  | { kind: "idle" }
  | { kind: "generating" }
  | { kind: "error"; message: string };

export default function LiveAssessmentPage() {
  return (
    <RequireAuth>
      <LiveAssessmentView />
    </RequireAuth>
  );
}

function LiveAssessmentView() {
  const params = useParams<{ assessmentId: string }>();
  const assessmentId = params.assessmentId;
  const router = useRouter();

  const [loadedAssessmentId, setLoadedAssessmentId] = React.useState(assessmentId);
  const [state, setState] = React.useState<LoadState>({ kind: "loading" });
  const [submitting, setSubmitting] = React.useState(false);
  const [generation, setGeneration] = React.useState<GenerationState>({ kind: "idle" });

  // Reset to loading during render when assessmentId changes, instead of
  // calling setState synchronously inside the effect body (React's
  // documented pattern for resetting state on a changed prop/param).
  if (assessmentId !== loadedAssessmentId) {
    setLoadedAssessmentId(assessmentId);
    setState({ kind: "loading" });
  }

  React.useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const session = await getAssessment(assessmentId);
        const goal = await getGoal(session.goal_id);
        if (!cancelled) {
          setState({ kind: "ready", session, goalText: goal.goal_text, lastAnswer: null });
        }
      } catch (error) {
        if (cancelled) {
          return;
        }
        if (error instanceof ApiError && error.status === 404) {
          setState({ kind: "not_found" });
          return;
        }
        if (error instanceof ApiError && error.status === 422) {
          setState({ kind: "invalid_id" });
          return;
        }
        const message =
          error instanceof ApiError ? error.message : "Unable to reach the PathAI backend.";
        setState({ kind: "error", message });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [assessmentId]);

  async function handleSubmit(payload: AssessmentAnswerCreate) {
    if (state.kind !== "ready") {
      return;
    }
    setSubmitting(true);
    try {
      const response = await submitAssessmentAnswer(assessmentId, payload);
      setState({
        kind: "ready",
        session: response.session,
        goalText: state.goalText,
        lastAnswer: response.answer,
      });
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "Unable to reach the PathAI backend.";
      setState({ kind: "error", message });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleGenerate(runId: string) {
    setGeneration({ kind: "generating" });
    try {
      await generateMyWorkspace();
      router.replace(`/dashboard/${runId}`);
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "Unable to reach the PathAI backend.";
      setGeneration({ kind: "error", message });
    }
  }

  if (state.kind === "loading") {
    return <LiveAssessmentSkeleton />;
  }

  if (state.kind === "not_found") {
    return <p className="text-muted-foreground text-sm">Assessment not found.</p>;
  }

  if (state.kind === "invalid_id") {
    return (
      <p className="text-muted-foreground text-sm">
        That doesn&apos;t look like a valid assessment ID.
      </p>
    );
  }

  if (state.kind === "error") {
    return (
      <Alert variant="destructive">
        <AlertTitle>Something went wrong</AlertTitle>
        <AlertDescription>{state.message}</AlertDescription>
      </Alert>
    );
  }

  const { session, goalText, lastAnswer } = state;

  if (session.status === "completed") {
    const generating = generation.kind === "generating";
    return (
      <div className="mx-auto flex max-w-lg flex-col gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Diagnostic complete</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <p className="text-muted-foreground text-sm">
              You answered {session.question_count} question
              {session.question_count === 1 ? "" : "s"} with {Math.round(session.confidence * 100)}%
              overall confidence. Let&apos;s build your personalized knowledge map and curriculum
              from your answers.
            </p>

            {generation.kind === "error" ? (
              <Alert variant="destructive">
                <AlertTitle>Couldn&apos;t generate your learning path</AlertTitle>
                <AlertDescription>{generation.message}</AlertDescription>
              </Alert>
            ) : null}

            <Button
              onClick={() => handleGenerate(session.run_id)}
              disabled={generating}
              className="w-fit"
            >
              {generating ? "Generating your learning path..." : "Generate my learning path"}
            </Button>

            {generation.kind === "error" ? (
              <button
                type="button"
                onClick={() => router.replace(`/dashboard/${session.run_id}`)}
                className="text-muted-foreground w-fit text-sm underline-offset-4 hover:underline"
              >
                Skip for now and view my dashboard
              </button>
            ) : null}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (session.current_question === null) {
    return (
      <p className="text-muted-foreground text-sm">
        This assessment isn&apos;t active right now.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
      <div className="flex flex-col gap-6">
        <LiveAssessmentHeader
          goalText={goalText}
          questionNumber={session.question_count + 1}
          totalQuestions={TOTAL_QUESTIONS}
          confidence={session.confidence}
        />

        {lastAnswer ? <PreviousAnswerBanner answer={lastAnswer} /> : null}

        <LiveQuestionCard
          key={session.current_question.question_id}
          question={session.current_question}
          questionNumber={session.question_count + 1}
          submitting={submitting}
          onSubmit={handleSubmit}
        />
      </div>

      <ConceptSidebar conceptEvidence={session.concept_evidence} />
    </div>
  );
}

function LiveAssessmentSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-3">
          <Skeleton className="h-3 w-40" />
          <Skeleton className="h-7 w-96 max-w-full" />
        </div>
        <Skeleton className="h-19 rounded-2xl" />
        <Skeleton className="h-72 rounded-2xl" />
      </div>
      <Skeleton className="h-96 rounded-2xl" />
    </div>
  );
}

"use client";

import * as React from "react";
import { useParams, usePathname, useRouter, useSearchParams } from "next/navigation";

import { RequireAuth } from "@/components/auth/require-auth";
import { QuestionPanel } from "@/components/assessment/question-panel";
import { QuestionTrail } from "@/components/assessment/question-trail";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/client";
import { getAssessment, getAssessmentAnswers } from "@/lib/api/assessment";
import { cn } from "@/lib/utils";
import type { AssessmentAnswerDTO, AssessmentSessionDTO, AssessmentStatus } from "@/lib/types/assessment";

type AssessmentLoadState =
  | { kind: "loading" }
  | { kind: "not_found" }
  | { kind: "invalid_id" }
  | { kind: "ready"; session: AssessmentSessionDTO; answers: AssessmentAnswerDTO[] }
  | { kind: "error"; message: string };

const STATUS_CONFIG: Record<AssessmentStatus, { label: string; className: string }> = {
  created: { label: "Created", className: "bg-surface-sunken text-tertiary" },
  in_progress: { label: "In progress", className: "bg-brand-tint text-brand" },
  completed: { label: "Completed", className: "bg-success-tint text-success" },
  failed: { label: "Failed", className: "bg-danger-tint text-danger" },
};

export default function AssessmentPage() {
  return (
    <RequireAuth>
      <React.Suspense fallback={<AssessmentSkeleton />}>
        <AssessmentView />
      </React.Suspense>
    </RequireAuth>
  );
}

function AssessmentView() {
  const params = useParams<{ assessmentId: string }>();
  const assessmentId = params.assessmentId;
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();

  const questionParam = searchParams.get("question");

  const [loadedAssessmentId, setLoadedAssessmentId] = React.useState(assessmentId);
  const [state, setState] = React.useState<AssessmentLoadState>({ kind: "loading" });

  if (assessmentId !== loadedAssessmentId) {
    setLoadedAssessmentId(assessmentId);
    setState({ kind: "loading" });
  }

  React.useEffect(() => {
    let cancelled = false;

    Promise.all([getAssessment(assessmentId), getAssessmentAnswers(assessmentId)])
      .then(([session, answers]) => {
        if (!cancelled) {
          setState({ kind: "ready", session, answers });
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
        // AssessmentId requires an "assessment_" prefix + pattern
        // (schemas/ids.py); a malformed id fails FastAPI's request
        // validation with 422 before reaching the not-found path.
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
  }, [assessmentId]);

  const navigateToQuestion = React.useCallback(
    (index: number) => {
      const next = new URLSearchParams(searchParams.toString());
      next.set("question", String(index));
      router.replace(`${pathname}?${next.toString()}`, { scroll: false });
    },
    [pathname, router, searchParams]
  );

  if (state.kind === "loading") {
    return <AssessmentSkeleton />;
  }

  if (state.kind === "error") {
    return (
      <Alert variant="destructive">
        <AlertTitle>Couldn&apos;t load this assessment</AlertTitle>
        <AlertDescription>{state.message}</AlertDescription>
      </Alert>
    );
  }

  if (state.kind === "invalid_id") {
    return (
      <p className="text-muted-foreground text-sm">
        That doesn&apos;t look like a valid assessment ID.
      </p>
    );
  }

  if (state.kind === "not_found") {
    return <p className="text-muted-foreground text-sm">Assessment not found.</p>;
  }

  const { session, answers } = state;

  if (answers.length === 0) {
    return (
      <div className="flex flex-col gap-8">
        <AssessmentHeader session={session} />
        <p className="text-muted-foreground text-sm">
          No answers have been recorded for this assessment yet.
        </p>
      </div>
    );
  }

  const requestedIndex = questionParam ? Number(questionParam) : 0;
  const selectedIndex = Number.isInteger(requestedIndex)
    ? Math.min(Math.max(requestedIndex, 0), answers.length - 1)
    : 0;
  const selectedAnswer = answers[selectedIndex]!;

  return (
    <div className="flex flex-col gap-8">
      <AssessmentHeader session={session} />

      <QuestionTrail
        answers={answers}
        questionCount={session.question_count}
        selectedIndex={selectedIndex}
        onSelectIndex={navigateToQuestion}
      />

      <QuestionPanel
        answer={selectedAnswer}
        index={selectedIndex}
        totalCount={answers.length}
        onNavigate={navigateToQuestion}
      />
    </div>
  );
}

function AssessmentHeader({ session }: { session: AssessmentSessionDTO }) {
  const status = STATUS_CONFIG[session.status];
  return (
    <div className="flex flex-wrap items-start justify-between gap-6">
      <div>
        <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
          Assessment
        </span>
        <h2 className="font-goal text-foreground mt-1 text-lg font-medium">
          Diagnostic Assessment
        </h2>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-tertiary font-mono text-[13px]">
          {Math.round(session.confidence * 100)}% confidence
        </span>
        <Badge className={cn("rounded-full px-3 py-1.5 text-sm", status.className)}>
          {status.label}
        </Badge>
      </div>
    </div>
  );
}

function AssessmentSkeleton() {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-3">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-7 w-72 max-w-full" />
      </div>
      <Skeleton className="h-[70px] rounded-2xl" />
      <div className="flex flex-col gap-4">
        <Skeleton className="h-9 w-96 max-w-full" />
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-16 rounded-2xl" />
        ))}
      </div>
    </div>
  );
}

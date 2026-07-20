"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { RequireAuth } from "@/components/auth/require-auth";
import { CompletionRing } from "@/components/progress/completion-ring";
import { NextActionCard } from "@/components/progress/next-action-card";
import { StuckEventList } from "@/components/progress/stuck-event-list";
import { TopicTrail } from "@/components/progress/topic-trail";
import type { TrailTopicInput } from "@/components/progress/topic-trail-geometry";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusPill } from "@/components/ui/status-pill";
import { ApiError } from "@/lib/api/client";
import { getCurriculum } from "@/lib/api/curriculum";
import { getProgress } from "@/lib/api/progress";
import { formatConceptLabel } from "@/lib/utils";
import type { CurriculumDTO } from "@/lib/types/curriculum";
import type { ProgressStateDTO, ProgressStatus } from "@/lib/types/progress";

type ProgressLoadState =
  | { kind: "loading" }
  | { kind: "not_found" }
  | { kind: "invalid_id" }
  | { kind: "ready"; progress: ProgressStateDTO; curriculum: CurriculumDTO }
  | { kind: "error"; message: string };

const STATUS_PILL_CONFIG: Record<ProgressStatus, { label: string; tone: "neutral" | "brand" | "warning" | "success" }> = {
  not_started: { label: "Not started", tone: "neutral" },
  in_progress: { label: "In progress", tone: "brand" },
  adaptation_needed: { label: "Needs a check-in", tone: "warning" },
  completed: { label: "Completed", tone: "success" },
};

const STATUS_HEADLINE: Record<ProgressStatus, string> = {
  not_started: "Ready to Begin",
  in_progress: "",
  adaptation_needed: "Your Plan Needs a Check-In",
  completed: "You've Completed This Path",
};

export default function ProgressTrackingPage() {
  return (
    <RequireAuth>
      <React.Suspense fallback={<ProgressSkeleton />}>
        <ProgressTrackingView />
      </React.Suspense>
    </RequireAuth>
  );
}

function ProgressTrackingView() {
  const params = useParams<{ progressId: string }>();
  const progressId = params.progressId;

  const [state, setState] = React.useState<ProgressLoadState>({ kind: "loading" });

  React.useEffect(() => {
    let cancelled = false;

    getProgress(progressId)
      .then(async (progress) => {
        const curriculum = await getCurriculum(progress.curriculum_id);
        if (!cancelled) {
          setState({ kind: "ready", progress, curriculum });
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
        // ProgressId requires a "progress_" prefix + pattern (schemas/ids.py);
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
  }, [progressId]);

  if (state.kind === "loading") {
    return <ProgressSkeleton />;
  }

  if (state.kind === "error") {
    return (
      <Alert variant="destructive">
        <AlertTitle>Couldn&apos;t load this progress state</AlertTitle>
        <AlertDescription>{state.message}</AlertDescription>
      </Alert>
    );
  }

  if (state.kind === "invalid_id") {
    return (
      <p className="text-muted-foreground text-sm">
        That doesn&apos;t look like a valid progress ID.
      </p>
    );
  }

  if (state.kind === "not_found") {
    return (
      <p className="text-muted-foreground text-sm">
        Progress tracking hasn&apos;t started for this curriculum yet. Come back once you&apos;ve
        worked through a topic or taken a quiz.
      </p>
    );
  }

  const { progress, curriculum } = state;
  const topicTitleById = new Map(
    curriculum.weeks.flatMap((week) => week.topics).map((topic) => [topic.topic_id, topic.title])
  );

  const trailTopics: TrailTopicInput[] = progress.topic_progress.map((topicProgress) => ({
    topicId: topicProgress.topic_id,
    title: topicTitleById.get(topicProgress.topic_id) ?? topicProgress.topic_id,
    status: topicProgress.status,
    completion: topicProgress.completion,
    isCurrent: topicProgress.topic_id === progress.current_topic_id,
    lastScore: topicProgress.last_score,
    attemptCount: topicProgress.attempt_count,
    stuckCount: topicProgress.stuck_count,
    notes: topicProgress.notes,
  }));

  const pillConfig = STATUS_PILL_CONFIG[progress.status];
  const headline =
    progress.status === "in_progress"
      ? `You're ${Math.round(progress.overall_completion * 100)}% Through`
      : STATUS_HEADLINE[progress.status];

  return (
    <div className="flex flex-col gap-9">
      <div className="flex items-center gap-3">
        <Link
          href={`/curriculum/${progress.curriculum_id}`}
          aria-label="Back to curriculum"
          className="border-border text-muted-foreground hover:bg-surface-sunken hover:text-foreground flex size-9 flex-none items-center justify-center rounded-full border"
        >
          <ArrowLeft className="size-4" />
        </Link>
        <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
          Progress · <span className="font-mono normal-case tracking-normal">{progress.curriculum_id}</span>
        </span>
      </div>

      <div>
        <h1 className="font-goal text-foreground max-w-lg text-3xl leading-tight font-medium italic">
          {headline}
        </h1>
        {progress.last_activity_at ? (
          <p className="text-tertiary mt-2.5 font-mono text-xs">
            Last activity {new Date(progress.last_activity_at).toLocaleString()}
          </p>
        ) : null}
      </div>

      <div className="flex flex-col items-center gap-4">
        <CompletionRing value={progress.overall_completion} />
        <StatusPill tone={pillConfig.tone}>{pillConfig.label}</StatusPill>
      </div>

      {progress.next_recommended_action ? (
        <NextActionCard action={progress.next_recommended_action} curriculumId={progress.curriculum_id} />
      ) : null}

      <div>
        <div className="text-tertiary mb-6 text-[13px] font-semibold tracking-wide uppercase">
          Topic trail
        </div>
        <TopicTrail topics={trailTopics} />
      </div>

      <StuckEventList events={progress.stuck_events} topicTitleById={topicTitleById} />

      {progress.weak_concepts.length > 0 ? (
        <div>
          <div className="text-tertiary mb-3.5 text-[13px] font-semibold tracking-wide uppercase">
            Weak concepts
          </div>
          <div className="flex flex-wrap gap-2.5">
            {progress.weak_concepts.map((conceptId) => (
              <span
                key={conceptId}
                className="border-border bg-card text-foreground inline-flex items-center rounded-full border px-3.5 py-1.5 text-[13px] font-medium"
              >
                {formatConceptLabel(conceptId)}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      <div className="border-border border-t pt-6 text-center">
        <Link
          href={`/curriculum/${progress.curriculum_id}`}
          className="text-brand text-sm font-semibold hover:underline"
        >
          View full curriculum <span aria-hidden="true">→</span>
        </Link>
      </div>
    </div>
  );
}

function ProgressSkeleton() {
  return (
    <div className="flex flex-col gap-9">
      <div className="flex items-center gap-3">
        <Skeleton className="size-9 rounded-full" />
        <Skeleton className="h-3 w-32" />
      </div>
      <div className="flex flex-col gap-2.5">
        <Skeleton className="h-9 w-72" />
        <Skeleton className="h-3 w-40" />
      </div>
      <div className="flex flex-col items-center gap-4">
        <Skeleton className="size-50 rounded-full" />
        <Skeleton className="h-7 w-28 rounded-full" />
      </div>
      <Skeleton className="h-24 w-full rounded-2xl" />
      <Skeleton className="h-64 w-full rounded-xl" />
      <Skeleton className="h-40 w-full rounded-xl" />
    </div>
  );
}

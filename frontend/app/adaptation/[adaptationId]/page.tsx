"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { ChangeCard } from "@/components/adaptation/change-card";
import { RerouteTrail } from "@/components/adaptation/reroute-trail";
import { TriggerCard } from "@/components/adaptation/trigger-card";
import { RequireAuth } from "@/components/auth/require-auth";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusPill } from "@/components/ui/status-pill";
import { ApiError } from "@/lib/api/client";
import { getAdaptation } from "@/lib/api/adaptation";
import { getCurriculum } from "@/lib/api/curriculum";
import type { AdaptationEventDTO, AdaptationStatus, AdaptationTriggerType } from "@/lib/types/adaptation";
import type { CurriculumDTO } from "@/lib/types/curriculum";

type AdaptationLoadState =
  | { kind: "loading" }
  | { kind: "not_found" }
  | { kind: "invalid_id" }
  | { kind: "ready"; event: AdaptationEventDTO; curriculum: CurriculumDTO }
  | { kind: "error"; message: string };

const STATUS_PILL_CONFIG: Record<AdaptationStatus, { label: string; tone: "brand" | "success" | "danger" }> = {
  proposed: { label: "Proposed", tone: "brand" },
  applied: { label: "Applied", tone: "success" },
  failed: { label: "Failed", tone: "danger" },
};

const TRIGGER_HEADLINE: Record<AdaptationTriggerType, string> = {
  quiz_score_below_threshold: "Your Plan Adjusted After a Quiz",
  stuck_event_threshold: "Your Plan Adjusted After Getting Stuck",
  critic_score_below_threshold: "Your Plan Adjusted After a Curriculum Review",
};

export default function AdaptationDetailPage() {
  return (
    <RequireAuth>
      <React.Suspense fallback={<AdaptationSkeleton />}>
        <AdaptationDetailView />
      </React.Suspense>
    </RequireAuth>
  );
}

function AdaptationDetailView() {
  const params = useParams<{ adaptationId: string }>();
  const adaptationId = params.adaptationId;

  const [state, setState] = React.useState<AdaptationLoadState>({ kind: "loading" });

  React.useEffect(() => {
    let cancelled = false;

    getAdaptation(adaptationId)
      .then(async (event) => {
        const curriculum = await getCurriculum(event.curriculum_id);
        if (!cancelled) {
          setState({ kind: "ready", event, curriculum });
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
        // AdaptationId requires an "adapt_" prefix + pattern (schemas/ids.py);
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
  }, [adaptationId]);

  if (state.kind === "loading") {
    return <AdaptationSkeleton />;
  }

  if (state.kind === "error") {
    return (
      <Alert variant="destructive">
        <AlertTitle>Couldn&apos;t load this adaptation</AlertTitle>
        <AlertDescription>{state.message}</AlertDescription>
      </Alert>
    );
  }

  if (state.kind === "invalid_id") {
    return (
      <p className="text-muted-foreground text-sm">
        That doesn&apos;t look like a valid adaptation ID.
      </p>
    );
  }

  if (state.kind === "not_found") {
    return (
      <p className="text-muted-foreground text-sm">
        No plan adjustments have happened for this curriculum yet.
      </p>
    );
  }

  const { event, curriculum } = state;
  const pillConfig = STATUS_PILL_CONFIG[event.status];
  const weekNumbers = curriculum.weeks.map((week) => week.week_number);
  const targetWeeks = event.changes
    .map((change) => change.target_week)
    .filter((week): week is number => week !== null);
  const updatedCurriculumId = event.new_curriculum_id ?? event.curriculum_id;

  return (
    <div className="flex flex-col gap-9">
      <div className="flex items-center gap-3">
        <Link
          href={`/curriculum/${event.curriculum_id}`}
          aria-label="Back to curriculum"
          className="border-border text-muted-foreground hover:bg-surface-sunken hover:text-foreground flex size-9 flex-none items-center justify-center rounded-full border"
        >
          <ArrowLeft className="size-4" />
        </Link>
        <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
          Adaptation · <span className="font-mono normal-case tracking-normal">{event.adaptation_event_id}</span>
        </span>
      </div>

      <div>
        <div className="flex flex-wrap items-start gap-3.5">
          <h1 className="font-goal text-foreground max-w-xl text-3xl leading-tight font-medium italic">
            {TRIGGER_HEADLINE[event.trigger_type]}
          </h1>
          <StatusPill tone={pillConfig.tone} className="mt-1.5">
            {pillConfig.label}
          </StatusPill>
        </div>
        <p className="text-tertiary mt-2.5 font-mono text-xs">
          {new Date(event.updated_at).toLocaleString()}
        </p>
      </div>

      <TriggerCard event={event} />

      <RerouteTrail weekNumbers={weekNumbers} targetWeeks={targetWeeks} />

      <div className="flex flex-col gap-4">
        <div className="border-border bg-card rounded-2xl border p-6 shadow-sm">
          <div className="text-tertiary mb-2.5 font-mono text-[11px] font-semibold tracking-wide uppercase">
            Before
          </div>
          <p className="font-goal text-foreground text-[17px] leading-relaxed italic">
            {event.before_summary}
          </p>
        </div>
        <div className="border-border bg-card rounded-2xl border p-6 shadow-sm">
          <div className="text-tertiary mb-2.5 font-mono text-[11px] font-semibold tracking-wide uppercase">
            After
          </div>
          <p className="font-goal text-foreground text-[17px] leading-relaxed italic">
            {event.after_summary}
          </p>
        </div>
      </div>

      <div>
        <div className="text-tertiary mb-3.5 text-[13px] font-semibold tracking-wide uppercase">
          What changed
        </div>
        <div className="flex flex-col gap-3.5">
          {event.changes.map((change, index) => (
            <ChangeCard key={`${change.change_type}-${change.target_week ?? "none"}-${index}`} change={change} />
          ))}
        </div>
      </div>

      <div className="border-border border-t pt-6">
        <Link
          href={`/curriculum/${updatedCurriculumId}`}
          className="text-brand text-sm font-semibold hover:underline"
        >
          View your updated curriculum <span aria-hidden="true">→</span>
        </Link>
      </div>
    </div>
  );
}

function AdaptationSkeleton() {
  return (
    <div className="flex flex-col gap-9">
      <div className="flex items-center gap-3">
        <Skeleton className="size-9 rounded-full" />
        <Skeleton className="h-3 w-32" />
      </div>
      <div className="flex flex-col gap-2.5">
        <Skeleton className="h-9 w-96" />
        <Skeleton className="h-3 w-40" />
      </div>
      <Skeleton className="h-20 w-full rounded-2xl" />
      <div className="grid grid-cols-2 gap-5">
        <Skeleton className="h-32 rounded-2xl" />
        <Skeleton className="h-32 rounded-2xl" />
      </div>
      <div className="flex flex-col gap-4">
        <Skeleton className="h-24 w-full rounded-2xl" />
        <Skeleton className="h-24 w-full rounded-2xl" />
      </div>
      <Skeleton className="h-40 w-full rounded-2xl" />
    </div>
  );
}

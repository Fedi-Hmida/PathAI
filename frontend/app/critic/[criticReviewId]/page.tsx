"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, ArrowRight, Check, Flag } from "lucide-react";

import { RequireAuth } from "@/components/auth/require-auth";
import { CriticRadarChart } from "@/components/critic/critic-radar-chart";
import { FindingsCard } from "@/components/critic/findings-card";
import { RevisionBadge } from "@/components/critic/revision-badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusPill } from "@/components/ui/status-pill";
import { ApiError } from "@/lib/api/client";
import { getCriticReview } from "@/lib/api/critic";
import type { CriticPassStatus, CriticReviewDTO } from "@/lib/types/critic";

type CriticLoadState =
  | { kind: "loading" }
  | { kind: "not_found" }
  | { kind: "invalid_id" }
  | { kind: "ready"; critic: CriticReviewDTO }
  | { kind: "error"; message: string };

const PASS_STATUS_CONFIG: Record<
  CriticPassStatus,
  { label: string; tone: "success" | "warning" | "brand" | "danger" }
> = {
  pass: { label: "Pass", tone: "success" },
  pass_with_warnings: { label: "Pass with warnings", tone: "warning" },
  revise: { label: "Revise", tone: "brand" },
  failed: { label: "Failed", tone: "danger" },
};

export default function CriticReviewDetailPage() {
  return (
    <RequireAuth>
      <React.Suspense fallback={<CriticReviewSkeleton />}>
        <CriticReviewView />
      </React.Suspense>
    </RequireAuth>
  );
}

function CriticReviewView() {
  const params = useParams<{ criticReviewId: string }>();
  const criticReviewId = params.criticReviewId;

  const [state, setState] = React.useState<CriticLoadState>({ kind: "loading" });

  React.useEffect(() => {
    let cancelled = false;

    getCriticReview(criticReviewId)
      .then((critic) => {
        if (!cancelled) {
          setState({ kind: "ready", critic });
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
        // CriticReviewId requires a "critic_" prefix + pattern
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
  }, [criticReviewId]);

  if (state.kind === "loading") {
    return <CriticReviewSkeleton />;
  }

  if (state.kind === "error") {
    return (
      <Alert variant="destructive">
        <AlertTitle>Couldn&apos;t load this critic review</AlertTitle>
        <AlertDescription>{state.message}</AlertDescription>
      </Alert>
    );
  }

  if (state.kind === "invalid_id") {
    return (
      <p className="text-muted-foreground text-sm">
        That doesn&apos;t look like a valid critic review ID.
      </p>
    );
  }

  if (state.kind === "not_found") {
    return <p className="text-muted-foreground text-sm">Critic review not found.</p>;
  }

  const { critic } = state;
  const passStatus = PASS_STATUS_CONFIG[critic.pass_status];

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center gap-3">
        <Link
          href={`/dashboard/${critic.run_id}`}
          aria-label="Back to dashboard"
          className="border-border text-muted-foreground hover:bg-surface-sunken hover:text-foreground flex size-9 flex-none items-center justify-center rounded-full border"
        >
          <ArrowLeft className="size-4" />
        </Link>
        <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
          Critic Review
        </span>
      </div>

      <div>
        <div className="flex flex-wrap items-baseline gap-3.5">
          <h1 className="font-goal text-foreground text-3xl leading-tight font-medium italic">
            Curriculum Review
          </h1>
          {critic.revision_attempt ? <RevisionBadge attempt={critic.revision_attempt} /> : null}
        </div>
        <p className="text-tertiary mt-2.5 font-mono text-xs">
          Created {new Date(critic.created_at).toLocaleDateString()}
        </p>
      </div>

      <div className="flex flex-col items-center gap-4">
        <CriticRadarChart
          dimensionScores={critic.dimension_scores}
          overallScore={critic.overall_score}
        />
        <StatusPill tone={passStatus.tone}>{passStatus.label}</StatusPill>
      </div>

      <div className="flex flex-wrap gap-5">
        <FindingsCard
          eyebrow="What's working"
          title="Strengths"
          items={critic.strengths}
          icon={Check}
          iconClassName="text-success"
          emptyMessage="No strengths recorded yet."
        />
        <FindingsCard
          eyebrow="What needs work"
          title="Issues"
          items={critic.issues}
          icon={Flag}
          iconClassName="text-warning"
          emptyMessage="No issues recorded yet."
        />
      </div>

      <FindingsCard
        title="If This Gets Reviewed Again"
        titleClassName="font-goal text-lg font-medium italic"
        items={critic.revision_recommendations}
        icon={ArrowRight}
        iconClassName="text-brand"
        emptyMessage="No revision recommendations yet."
      />

      <div className="border-border border-t pt-6">
        <Link
          href={`/curriculum/${critic.curriculum_id}`}
          className="text-brand inline-flex items-center gap-1.5 text-sm font-semibold hover:underline"
        >
          View the reviewed curriculum <span aria-hidden="true">→</span>
        </Link>
      </div>
    </div>
  );
}

function CriticReviewSkeleton() {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center gap-3">
        <Skeleton className="size-9 rounded-full" />
        <Skeleton className="h-3 w-24" />
      </div>
      <div className="flex flex-col gap-2.5">
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-3 w-40" />
      </div>
      <div className="flex flex-col items-center gap-4">
        <Skeleton className="size-[380px] rounded-full" />
        <Skeleton className="h-7 w-32 rounded-full" />
      </div>
      <div className="flex flex-wrap gap-5">
        <Skeleton className="h-40 flex-1 rounded-xl" />
        <Skeleton className="h-40 flex-1 rounded-xl" />
      </div>
      <Skeleton className="h-32 w-full rounded-xl" />
    </div>
  );
}

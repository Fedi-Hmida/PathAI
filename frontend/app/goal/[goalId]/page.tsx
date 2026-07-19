"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Check, Flag } from "lucide-react";

import { RequireAuth } from "@/components/auth/require-auth";
import { LifecycleStamps } from "@/components/goal/lifecycle-stamps";
import { ProfileGrid } from "@/components/goal/profile-grid";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/client";
import { getGoal } from "@/lib/api/goal";
import { formatConceptLabel } from "@/lib/utils";
import type { LearningGoalDTO } from "@/lib/types/goal";

type GoalLoadState =
  | { kind: "loading" }
  | { kind: "not_found" }
  | { kind: "invalid_id" }
  | { kind: "ready"; goal: LearningGoalDTO }
  | { kind: "error"; message: string };

export default function GoalDetailPage() {
  return (
    <RequireAuth>
      <React.Suspense fallback={<GoalDetailSkeleton />}>
        <GoalDetailView />
      </React.Suspense>
    </RequireAuth>
  );
}

function GoalDetailView() {
  const params = useParams<{ goalId: string }>();
  const goalId = params.goalId;

  const [state, setState] = React.useState<GoalLoadState>({ kind: "loading" });

  React.useEffect(() => {
    let cancelled = false;

    getGoal(goalId)
      .then((goal) => {
        if (!cancelled) {
          setState({ kind: "ready", goal });
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
        // GoalId requires a "goal_" prefix + pattern (schemas/ids.py); a
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
  }, [goalId]);

  if (state.kind === "loading") {
    return <GoalDetailSkeleton />;
  }

  if (state.kind === "error") {
    return (
      <Alert variant="destructive">
        <AlertTitle>Couldn&apos;t load this goal</AlertTitle>
        <AlertDescription>{state.message}</AlertDescription>
      </Alert>
    );
  }

  if (state.kind === "invalid_id") {
    return (
      <p className="text-muted-foreground text-sm">That doesn&apos;t look like a valid goal ID.</p>
    );
  }

  if (state.kind === "not_found") {
    return <p className="text-muted-foreground text-sm">Goal not found.</p>;
  }

  const { goal } = state;
  const profile = goal.learner_profile;

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center gap-3">
        <Link
          href={`/dashboard/${goal.run_id}`}
          aria-label="Back to dashboard"
          className="border-border text-muted-foreground hover:bg-surface-sunken hover:text-foreground flex size-9 flex-none items-center justify-center rounded-full border"
        >
          <ArrowLeft className="size-4" />
        </Link>
        <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
          Goal
        </span>
      </div>

      <div className="bg-card border-border rounded-xl border-[1.5px] px-6 py-8 shadow-sm sm:px-10">
        <LifecycleStamps status={goal.status} />
        <p className="font-goal text-foreground mx-auto mt-8 max-w-xl text-center text-2xl leading-snug font-medium text-pretty italic">
          {goal.goal_text}
        </p>
      </div>

      <p className="text-tertiary text-center font-mono text-xs">
        Created {new Date(goal.created_at).toLocaleDateString()}
      </p>

      <ProfileGrid
        learnerType={profile.learner_type}
        desiredOutcome={profile.desired_outcome}
        timeAvailabilityHoursPerWeek={profile.time_availability_hours_per_week}
        targetDurationWeeks={goal.target_duration_weeks}
        hoursPerWeek={goal.hours_per_week}
        difficultyTarget={profile.difficulty_target}
      />

      <div className="flex flex-wrap gap-5">
        <Card className="min-w-70 flex-1">
          <CardHeader>
            <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
              What&apos;s working
            </span>
            <CardTitle>Strengths</CardTitle>
          </CardHeader>
          <CardContent>
            {profile.strengths.length > 0 ? (
              <ul className="flex flex-col gap-2.5">
                {profile.strengths.map((strength) => (
                  <li key={strength} className="text-foreground flex items-center gap-2 text-sm">
                    <Check className="text-success size-4 flex-none" />
                    {strength}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-muted-foreground text-sm">No strengths recorded yet.</p>
            )}
          </CardContent>
        </Card>

        <Card className="min-w-70 flex-1">
          <CardHeader>
            <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
              Needs work
            </span>
            <CardTitle>Weak areas</CardTitle>
          </CardHeader>
          <CardContent>
            {profile.weak_areas.length > 0 ? (
              <ul className="flex flex-col gap-2.5">
                {profile.weak_areas.map((area) => (
                  <li key={area} className="text-foreground flex items-center gap-2 text-sm">
                    <Flag className="text-warning size-4 flex-none" />
                    {area}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-muted-foreground text-sm">No weak areas recorded yet.</p>
            )}
          </CardContent>
        </Card>
      </div>

      <div>
        <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
          Preferred resources
        </span>
        <div className="mt-2.5 flex flex-wrap gap-2">
          {profile.preferred_resource_types.length > 0 ? (
            profile.preferred_resource_types.map((resourceType) => (
              <span
                key={resourceType}
                className="border-border text-muted-foreground rounded-full border px-3 py-1.5 text-[13px]"
              >
                {formatConceptLabel(resourceType)}
              </span>
            ))
          ) : (
            <p className="text-muted-foreground mt-0 text-sm">
              No preferred resource types recorded yet.
            </p>
          )}
        </div>
        {goal.constraints.length > 0 ? (
          <ul className="mt-3.5 flex flex-col gap-1.5">
            {goal.constraints.map((constraint) => (
              <li key={constraint} className="text-muted-foreground flex gap-2 text-[13px]">
                <span className="text-tertiary">–</span>
                {constraint}
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </div>
  );
}

function GoalDetailSkeleton() {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center gap-3">
        <Skeleton className="size-9 rounded-full" />
        <Skeleton className="h-3 w-12" />
      </div>
      <Skeleton className="h-52 w-full rounded-xl" />
      <Skeleton className="mx-auto h-3 w-40" />
      <div className="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-6">
        <Skeleton className="h-16 rounded-lg" />
        <Skeleton className="h-16 rounded-lg" />
        <Skeleton className="h-16 rounded-lg" />
        <Skeleton className="h-16 rounded-lg" />
      </div>
      <div className="flex flex-wrap gap-5">
        <Skeleton className="h-40 flex-1 rounded-xl" />
        <Skeleton className="h-40 flex-1 rounded-xl" />
      </div>
    </div>
  );
}

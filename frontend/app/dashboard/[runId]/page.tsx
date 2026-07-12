"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import { CheckCircle2, Link2, ShieldAlert } from "lucide-react";

import { RequireAuth } from "@/components/auth/require-auth";
import { AdaptationBanner } from "@/components/dashboard/adaptation-banner";
import { CurriculumWeekList } from "@/components/dashboard/curriculum-week-list";
import { KnowledgeMapCard } from "@/components/dashboard/knowledge-map-card";
import { KpiTile, type KpiTone } from "@/components/dashboard/kpi-tile";
import { NextActionCard } from "@/components/dashboard/next-action-card";
import { ProgressRing } from "@/components/dashboard/progress-ring";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/client";
import { getDashboard } from "@/lib/api/dashboard";
import { cn } from "@/lib/utils";
import type {
  CriticPassStatus,
  DashboardPayload,
  EvaluationPassStatus,
  GoalStatus,
  OrchestrationStatus,
} from "@/lib/types/dashboard";

type LoadState =
  | { kind: "loading" }
  | { kind: "ready"; dashboard: DashboardPayload }
  | { kind: "error"; message: string };

const RUN_STATUS_CONFIG: Record<OrchestrationStatus, { label: string; className: string }> = {
  queued: { label: "Queued", className: "bg-surface-sunken text-tertiary" },
  running: { label: "Running", className: "bg-brand-tint text-brand" },
  waiting_for_user: { label: "Needs input", className: "bg-warning-tint text-warning" },
  completed: { label: "Completed", className: "bg-success-tint text-success" },
  failed: { label: "Failed", className: "bg-danger-tint text-danger" },
  cancelled: { label: "Cancelled", className: "bg-surface-sunken text-tertiary" },
};

const GOAL_STATUS_LABEL: Record<GoalStatus, string> = {
  created: "Goal created",
  assessment_started: "Assessment in progress",
  curriculum_generated: "Curriculum generated",
  active: "Active goal",
  completed: "Goal completed",
  failed: "Goal failed",
};

const CRITIC_PASS_CONFIG: Record<CriticPassStatus, { label: string; tone: KpiTone }> = {
  pass: { label: "Pass", tone: "success" },
  pass_with_warnings: { label: "Pass with warnings", tone: "warning" },
  revise: { label: "Needs revision", tone: "warning" },
  failed: { label: "Failed", tone: "danger" },
};

const EVALUATION_PASS_CONFIG: Record<EvaluationPassStatus, { label: string; tone: KpiTone }> = {
  pass: { label: "Passed", tone: "success" },
  pass_with_warnings: { label: "Pass with warnings", tone: "warning" },
  fail: { label: "Failed", tone: "danger" },
};

function formatScore(score: number | null | undefined): string {
  return score == null ? "—" : score.toFixed(2);
}

export default function DashboardPage() {
  return (
    <RequireAuth>
      <DashboardView />
    </RequireAuth>
  );
}

function DashboardView() {
  const params = useParams<{ runId: string }>();
  const runId = params.runId;
  const [loadedRunId, setLoadedRunId] = React.useState(runId);
  const [state, setState] = React.useState<LoadState>({ kind: "loading" });

  // Reset to loading during render when runId changes, instead of calling
  // setState synchronously inside the effect body (React's documented
  // pattern for resetting state on a changed prop/param).
  if (runId !== loadedRunId) {
    setLoadedRunId(runId);
    setState({ kind: "loading" });
  }

  React.useEffect(() => {
    let cancelled = false;

    getDashboard(runId)
      .then((dashboard) => {
        if (!cancelled) {
          setState({ kind: "ready", dashboard });
        }
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        const message =
          error instanceof ApiError ? error.message : "Unable to reach the PathAI backend.";
        setState({ kind: "error", message });
      });

    return () => {
      cancelled = true;
    };
  }, [runId]);

  if (state.kind === "loading") {
    return <DashboardSkeleton />;
  }

  if (state.kind === "error") {
    return (
      <Alert variant="destructive">
        <AlertTitle>Couldn&apos;t load this run</AlertTitle>
        <AlertDescription>{state.message}</AlertDescription>
      </Alert>
    );
  }

  const { dashboard } = state;
  const runStatus = RUN_STATUS_CONFIG[dashboard.run_summary.status];
  const quiz = dashboard.quiz_summary;
  const critic = dashboard.critic_summary;
  const evaluation = dashboard.evaluation_summary;
  const resources = dashboard.resources_summary;

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-wrap items-start justify-between gap-6">
        <div className="max-w-2xl">
          <div className="text-tertiary mb-2 text-[11px] font-semibold tracking-widest uppercase">
            {GOAL_STATUS_LABEL[dashboard.goal_summary.status]}
          </div>
          <h1 className="font-goal text-foreground text-[32px] leading-snug font-medium italic">
            {dashboard.goal_summary.text}
          </h1>
        </div>
        <Badge className={cn("rounded-full px-3 py-1.5 text-sm", runStatus.className)}>
          {runStatus.label}
        </Badge>
      </div>

      {dashboard.ui_flags.show_adaptation_alert ? (
        <AdaptationBanner adaptationSummary={dashboard.adaptation_summary} />
      ) : null}

      <div className="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-5">
        <Card className="items-center gap-2 px-5 py-5">
          <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
            Completion
          </span>
          <div className="flex flex-1 items-center justify-center pt-1">
            <ProgressRing value={dashboard.progress_summary?.completion_percentage ?? 0} />
          </div>
        </Card>

        <KpiTile
          label="Quiz"
          value={formatScore(quiz?.latest_score)}
          statusText={
            quiz === null
              ? "No quiz attempts yet"
              : quiz.weak_concepts.length > 0
                ? `${quiz.weak_concepts.length} concept${quiz.weak_concepts.length === 1 ? "" : "s"} to review`
                : undefined
          }
          tone="neutral"
        />

        <KpiTile
          label="Critic"
          value={formatScore(critic?.overall_score)}
          statusText={
            critic?.pass_status
              ? CRITIC_PASS_CONFIG[critic.pass_status].label
              : "Not reviewed yet"
          }
          tone={critic?.pass_status ? CRITIC_PASS_CONFIG[critic.pass_status].tone : "neutral"}
          icon={ShieldAlert}
        />

        <KpiTile
          label="Evaluation"
          value={formatScore(evaluation?.overall_score)}
          statusText={
            evaluation?.pass_status
              ? EVALUATION_PASS_CONFIG[evaluation.pass_status].label
              : "Not evaluated yet"
          }
          tone={
            evaluation?.pass_status ? EVALUATION_PASS_CONFIG[evaluation.pass_status].tone : "neutral"
          }
          icon={CheckCircle2}
        />

        <KpiTile
          label="Resources"
          value={resources ? String(resources.total_attached) : "—"}
          statusText={
            resources?.average_relevance != null
              ? `${formatScore(resources.average_relevance)} avg relevance`
              : resources
                ? undefined
                : "No resources yet"
          }
          tone="neutral"
          icon={Link2}
        />
      </div>

      <div className="flex flex-wrap items-stretch gap-5">
        <KnowledgeMapCard
          knowledgeMapSummary={dashboard.knowledge_map_summary}
          assessmentId={dashboard.navigation_summary.artifact_ids.assessment_id ?? null}
          knowledgeMapId={dashboard.navigation_summary.artifact_ids.knowledge_map_id ?? null}
        />
        <NextActionCard progressSummary={dashboard.progress_summary} />
      </div>

      <CurriculumWeekList
        curriculumSummary={dashboard.curriculum_summary}
        currentTopic={dashboard.progress_summary?.current_topic ?? null}
        navigationSummary={dashboard.navigation_summary}
      />
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-start justify-between gap-6">
        <div className="flex flex-col gap-3">
          <Skeleton className="h-3 w-32" />
          <Skeleton className="h-9 w-[420px] max-w-full" />
        </div>
        <Skeleton className="h-7 w-24 rounded-full" />
      </div>
      <div className="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-5">
        {Array.from({ length: 5 }).map((_, index) => (
          <Skeleton key={index} className="h-[140px] rounded-2xl" />
        ))}
      </div>
      <div className="flex flex-wrap gap-5">
        <Skeleton className="h-[320px] flex-[2_1_520px] rounded-2xl" />
        <Skeleton className="h-[320px] flex-1 rounded-2xl" />
      </div>
      <Skeleton className="h-[260px] rounded-2xl" />
    </div>
  );
}

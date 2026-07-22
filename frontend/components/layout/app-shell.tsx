"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bot,
  BookOpen,
  CheckCircle2,
  ClipboardList,
  HelpCircle,
  LayoutDashboard,
  Link2,
  Network,
  PanelLeftClose,
  PanelLeftOpen,
  RefreshCw,
  ShieldAlert,
  Target,
  TrendingUp,
  Workflow,
  type LucideIcon,
} from "lucide-react";

import { AuthStatus } from "@/components/auth/auth-status";
import { useAuth } from "@/components/auth/auth-provider";
import { SplashScreen } from "@/components/layout/splash-screen";
import { CollapsingLabel, SIDEBAR_TRANSITION } from "@/components/layout/sidebar-primitives";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { getDashboard } from "@/lib/api/dashboard";
import { getMyWorkspace } from "@/lib/api/workspace";
import { cn } from "@/lib/utils";

// Screens with no route yet (empty components/<name>/ scaffolding, no
// app/<name>/ page). Shown in the sidebar as inactive placeholders so their
// planned position is visible, per product decision — not a RULES.md
// requirement.
const COMING_SOON_LINKS: { label: string; icon: LucideIcon }[] = [
  { label: "Evaluation", icon: CheckCircle2 },
  { label: "Agents", icon: Bot },
];

function SidebarLink({
  href,
  icon: Icon,
  label,
  active,
  open,
}: {
  href: string;
  icon: LucideIcon;
  label: string;
  active: boolean;
  open: boolean;
}) {
  return (
    <Link
      href={href}
      title={open ? undefined : label}
      className={cn(
        "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
        active ? "bg-surface-sunken text-foreground" : "text-muted-foreground hover:bg-surface-sunken hover:text-foreground"
      )}
    >
      <Icon className="size-4 flex-none" />
      <CollapsingLabel open={open}>{label}</CollapsingLabel>
    </Link>
  );
}

function SidebarLinkDisabled({
  icon: Icon,
  label,
  open,
  reason,
}: {
  icon: LucideIcon;
  label: string;
  open: boolean;
  reason: string;
}) {
  return (
    <div
      title={reason}
      aria-disabled="true"
      className="text-muted-foreground/50 flex cursor-not-allowed items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium"
    >
      <Icon className="size-4 flex-none" />
      <CollapsingLabel open={open}>{label}</CollapsingLabel>
    </div>
  );
}

function SectionLabel({ open, children }: { open: boolean; children: React.ReactNode }) {
  if (!open) {
    return <div className="border-border/60 mx-3 my-2 border-t" />;
  }
  return (
    <div className="text-tertiary mt-4 mb-1 px-3 text-[11px] font-semibold tracking-widest uppercase">
      {children}
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { status } = useAuth();
  const [open, setOpen] = React.useState(true);
  const [artifactIds, setArtifactIds] = React.useState<Record<string, string> | null>(null);
  // Only ever set from the async workspace lookup below; the
  // not-yet-authenticated case is a pure derived value (no effect needed).
  const [ownWorkspaceRunId, setOwnWorkspaceRunId] = React.useState<string | null>(null);

  const needsOwnWorkspace = status === "authenticated";
  const ownRunId = needsOwnWorkspace ? ownWorkspaceRunId : null;

  // Each caller has their own run, resolved via their workspace rather than
  // a fixed ID.
  React.useEffect(() => {
    if (!needsOwnWorkspace) {
      return;
    }
    let cancelled = false;
    getMyWorkspace()
      .then((workspace) => {
        if (!cancelled) {
          setOwnWorkspaceRunId(workspace?.run_id ?? null);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setOwnWorkspaceRunId(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [needsOwnWorkspace]);

  // Sidebar links for the drill-down screens (Knowledge Map, Assessment,
  // Curriculum) need real artifact IDs, not just the run ID — there is no
  // run-listing screen, so this fetches the resolved run's dashboard once to
  // resolve them. Until this resolves (or an ID is missing), those links
  // render inactive instead of pointing at a 404.
  const [loadedArtifactsForRunId, setLoadedArtifactsForRunId] = React.useState<string | null>(null);
  if (ownRunId !== loadedArtifactsForRunId) {
    setLoadedArtifactsForRunId(ownRunId);
    setArtifactIds(null);
  }

  React.useEffect(() => {
    if (!ownRunId) {
      return;
    }
    let cancelled = false;
    getDashboard(ownRunId)
      .then((dashboard) => {
        if (!cancelled) {
          setArtifactIds(dashboard.navigation_summary.artifact_ids);
        }
      })
      .catch(() => {
        // Sidebar degrades to inactive links; the page body already
        // surfaces its own error state for unreachable backends.
      });
    return () => {
      cancelled = true;
    };
  }, [ownRunId]);

  const [section, pathRunId] = pathname.split("/").filter(Boolean);
  // Section links preserve whatever runId is in the current URL when on a
  // run-scoped screen (this is always correct since the URL itself already
  // carries the caller's own run once they're on it), and fall back to the
  // resolved own run everywhere else (e.g. the contextual /curriculum/*
  // drill-down, which has no runId of its own). Null until the caller's own
  // workspace has resolved.
  const runId =
    (section === "dashboard" || section === "orchestration") && pathRunId
      ? pathRunId
      : ownRunId;

  const knowledgeMapId = artifactIds?.knowledge_map_id;
  const assessmentId = artifactIds?.assessment_id;
  const curriculumId = artifactIds?.curriculum_id;
  const goalId = artifactIds?.goal_id;
  const criticReviewId = artifactIds?.critic_review_id;
  const quizId = artifactIds?.quiz_id;
  const quizAttemptId = artifactIds?.quiz_attempt_id;
  const progressStateId = artifactIds?.progress_state_id;
  const adaptationEventId = artifactIds?.adaptation_event_id;

  if (status === "loading") {
    return <SplashScreen />;
  }

  if (status === "anonymous") {
    return <div className="flex min-h-screen items-center justify-center px-4 py-8">{children}</div>;
  }

  return (
    <div className="flex min-h-screen">
      <aside
        className={cn(
          "bg-card sticky top-0 flex h-screen flex-none flex-col overflow-hidden border-r",
          open ? "w-60" : "w-16"
        )}
        style={{ transition: `width ${SIDEBAR_TRANSITION}` }}
      >
        <div className="flex h-14 flex-none items-center justify-between px-4">
          <Link href="/" className="flex items-center text-sm font-semibold tracking-tight">
            <span>P</span>
            <CollapsingLabel open={open}>athAI</CollapsingLabel>
          </Link>
          <button
            type="button"
            onClick={() => setOpen((value) => !value)}
            aria-label={open ? "Collapse sidebar" : "Expand sidebar"}
            className="text-muted-foreground hover:bg-surface-sunken hover:text-foreground flex-none rounded-md p-1.5"
          >
            {open ? <PanelLeftClose className="size-4" /> : <PanelLeftOpen className="size-4" />}
          </button>
        </div>

        <nav className="scrollbar-thin flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto px-3 py-2">
          {runId ? (
            <SidebarLink
              href={`/dashboard/${runId}`}
              icon={LayoutDashboard}
              label="Dashboard"
              active={section === "dashboard"}
              open={open}
            />
          ) : (
            <SidebarLinkDisabled
              icon={LayoutDashboard}
              label="Dashboard"
              open={open}
              reason="Create a workspace to get started"
            />
          )}
          {goalId ? (
            <SidebarLink
              href={`/goal/${goalId}`}
              icon={Target}
              label="Goal"
              active={section === "goal"}
              open={open}
            />
          ) : (
            <SidebarLinkDisabled icon={Target} label="Goal" open={open} reason="Not available yet" />
          )}
          {knowledgeMapId ? (
            <SidebarLink
              href={`/knowledge-map/${knowledgeMapId}`}
              icon={Network}
              label="Knowledge Map"
              active={section === "knowledge-map"}
              open={open}
            />
          ) : (
            <SidebarLinkDisabled
              icon={Network}
              label="Knowledge Map"
              open={open}
              reason="Not available yet"
            />
          )}
          {assessmentId ? (
            <SidebarLink
              href={`/assessment/${assessmentId}`}
              icon={ClipboardList}
              label="Assessment"
              active={section === "assessment"}
              open={open}
            />
          ) : (
            <SidebarLinkDisabled
              icon={ClipboardList}
              label="Assessment"
              open={open}
              reason="Not available yet"
            />
          )}
          {curriculumId ? (
            <SidebarLink
              href={`/curriculum/${curriculumId}`}
              icon={BookOpen}
              label="Curriculum"
              active={section === "curriculum"}
              open={open}
            />
          ) : (
            <SidebarLinkDisabled
              icon={BookOpen}
              label="Curriculum"
              open={open}
              reason="Not available yet"
            />
          )}
          {curriculumId ? (
            <SidebarLink
              href={`/resources/${curriculumId}`}
              icon={Link2}
              label="Resources"
              active={section === "resources"}
              open={open}
            />
          ) : (
            <SidebarLinkDisabled icon={Link2} label="Resources" open={open} reason="Not available yet" />
          )}
          {quizId ? (
            <SidebarLink
              href={
                quizAttemptId
                  ? `/quiz/${quizId}/attempts/${quizAttemptId}`
                  : `/quiz/${quizId}/take`
              }
              icon={HelpCircle}
              label="Quiz"
              active={section === "quiz"}
              open={open}
            />
          ) : (
            <SidebarLinkDisabled
              icon={HelpCircle}
              label="Quiz"
              open={open}
              reason="Generate your curriculum to unlock the quiz"
            />
          )}
          {criticReviewId ? (
            <SidebarLink
              href={`/critic/${criticReviewId}`}
              icon={ShieldAlert}
              label="Critic Review"
              active={section === "critic"}
              open={open}
            />
          ) : (
            <SidebarLinkDisabled
              icon={ShieldAlert}
              label="Critic Review"
              open={open}
              reason="Not available yet"
            />
          )}
          {runId ? (
            <SidebarLink
              href={`/orchestration/${runId}`}
              icon={Workflow}
              label="Orchestration"
              active={section === "orchestration"}
              open={open}
            />
          ) : (
            <SidebarLinkDisabled
              icon={Workflow}
              label="Orchestration"
              open={open}
              reason="Create a workspace to get started"
            />
          )}

          {progressStateId ? (
            <SidebarLink
              href={`/progress/${progressStateId}`}
              icon={TrendingUp}
              label="Progress"
              active={section === "progress"}
              open={open}
            />
          ) : (
            <SidebarLinkDisabled
              icon={TrendingUp}
              label="Progress"
              open={open}
              reason="No progress tracked yet"
            />
          )}
          {adaptationEventId ? (
            <SidebarLink
              href={`/adaptation/${adaptationEventId}`}
              icon={RefreshCw}
              label="Adaptation"
              active={section === "adaptation"}
              open={open}
            />
          ) : (
            <SidebarLinkDisabled
              icon={RefreshCw}
              label="Adaptation"
              open={open}
              reason="No plan adjustments yet"
            />
          )}

          <SectionLabel open={open}>Coming soon</SectionLabel>
          {COMING_SOON_LINKS.map(({ label, icon }) => (
            <SidebarLinkDisabled key={label} icon={icon} label={label} open={open} reason="Coming soon" />
          ))}
        </nav>

        {/* Not bottom-pinned: in `next dev`, Next.js renders its own
            floating indicator fixed to the viewport's bottom-left corner,
            which would otherwise sit on top of and intercept clicks on
            whatever sidebar control lives there. */}
        <div className="border-border/60 mx-3 mt-1 flex flex-none flex-col gap-1 border-t px-0 py-3">
          <ThemeToggle open={open} />
          <AuthStatus open={open} />
        </div>
      </aside>

      <main className="min-w-0 flex-1 px-4 py-8">
        <div className="mx-auto w-full max-w-5xl">{children}</div>
      </main>
    </div>
  );
}

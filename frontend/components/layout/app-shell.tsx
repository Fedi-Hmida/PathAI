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

import { ThemeToggle } from "@/components/layout/theme-toggle";
import { getDashboard } from "@/lib/api/dashboard";
import { cn } from "@/lib/utils";
import { DEMO_RUN_ID } from "@/lib/types/orchestration";

const SIDEBAR_TRANSITION = "var(--duration-slow) var(--ease-standard)";

// Screens with no route yet (empty components/<name>/ scaffolding, no
// app/<name>/ page). Shown in the sidebar as inactive placeholders so their
// planned position is visible, per product decision — not a RULES.md
// requirement.
const COMING_SOON_LINKS: { label: string; icon: LucideIcon }[] = [
  { label: "Goal", icon: Target },
  { label: "Progress", icon: TrendingUp },
  { label: "Resources", icon: Link2 },
  { label: "Quiz", icon: HelpCircle },
  { label: "Adaptation", icon: RefreshCw },
  { label: "Critic Review", icon: ShieldAlert },
  { label: "Evaluation", icon: CheckCircle2 },
  { label: "Agents", icon: Bot },
];

function CollapsingLabel({ open, children }: { open: boolean; children: React.ReactNode }) {
  return (
    <span
      className={cn("overflow-hidden whitespace-nowrap", open ? "max-w-[160px] opacity-100" : "max-w-0 opacity-0")}
      style={{ transition: `max-width ${SIDEBAR_TRANSITION}, opacity ${SIDEBAR_TRANSITION}` }}
    >
      {children}
    </span>
  );
}

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
  const [open, setOpen] = React.useState(true);
  const [artifactIds, setArtifactIds] = React.useState<Record<string, string> | null>(null);

  // Sidebar links for the drill-down screens (Knowledge Map, Assessment,
  // Curriculum) need real artifact IDs, not just the demo run ID — there is
  // no run-listing screen, so this fetches the one canonical demo run's
  // dashboard once to resolve them. Until this resolves (or an ID is
  // missing), those links render inactive instead of pointing at a 404.
  React.useEffect(() => {
    let cancelled = false;
    getDashboard(DEMO_RUN_ID)
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
  }, []);

  const [section, pathRunId] = pathname.split("/").filter(Boolean);
  // This is a single-tenant, no-auth demo with exactly one meaningful
  // orchestration run (no run-listing screen exists or is planned). Section
  // links preserve whatever runId is in the current URL when on a
  // run-scoped screen, and fall back to the canonical demo run everywhere
  // else (e.g. the contextual /curriculum/* drill-down, which has no runId
  // of its own).
  const runId =
    (section === "dashboard" || section === "orchestration") && pathRunId
      ? pathRunId
      : DEMO_RUN_ID;

  const knowledgeMapId = artifactIds?.knowledge_map_id;
  const assessmentId = artifactIds?.assessment_id;
  const curriculumId = artifactIds?.curriculum_id;

  return (
    <div className="flex min-h-screen">
      <aside
        className={cn("bg-card sticky top-0 flex h-screen flex-none flex-col border-r", open ? "w-60" : "w-16")}
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

        <nav className="flex flex-col gap-1 px-3 py-2">
          <SidebarLink
            href={`/dashboard/${runId}`}
            icon={LayoutDashboard}
            label="Dashboard"
            active={section === "dashboard"}
            open={open}
          />
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
          <SidebarLink
            href={`/orchestration/${runId}`}
            icon={Workflow}
            label="Orchestration"
            active={section === "orchestration"}
            open={open}
          />

          <SectionLabel open={open}>Coming soon</SectionLabel>
          {COMING_SOON_LINKS.map(({ label, icon }) => (
            <SidebarLinkDisabled key={label} icon={icon} label={label} open={open} reason="Coming soon" />
          ))}
        </nav>

        {/* Not bottom-pinned: in `next dev`, Next.js renders its own
            floating indicator fixed to the viewport's bottom-left corner,
            which would otherwise sit on top of and intercept clicks on
            whatever sidebar control lives there. */}
        <div className="border-border/60 mx-3 mt-1 flex-none border-t px-0 py-3">
          <ThemeToggle />
        </div>
      </aside>

      <main className="min-w-0 flex-1 px-4 py-8">
        <div className="mx-auto w-full max-w-5xl">{children}</div>
      </main>
    </div>
  );
}

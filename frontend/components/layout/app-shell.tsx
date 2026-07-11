"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, PanelLeftClose, PanelLeftOpen, Workflow, type LucideIcon } from "lucide-react";

import { ThemeToggle } from "@/components/layout/theme-toggle";
import { cn } from "@/lib/utils";
import { DEMO_RUN_ID } from "@/lib/types/orchestration";

const SIDEBAR_TRANSITION = "var(--duration-slow) var(--ease-standard)";

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

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = React.useState(true);

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
            active={section === "dashboard" || section === "curriculum"}
            open={open}
          />
          <SidebarLink
            href={`/orchestration/${runId}`}
            icon={Workflow}
            label="Orchestration"
            active={section === "orchestration"}
            open={open}
          />
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

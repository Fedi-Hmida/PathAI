"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { ThemeToggle } from "@/components/layout/theme-toggle";
import { cn } from "@/lib/utils";
import { DEMO_RUN_ID } from "@/lib/types/orchestration";

function NavLink({
  href,
  active,
  children,
}: {
  href: string;
  active: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
        active ? "bg-surface-sunken text-foreground" : "text-muted-foreground hover:text-foreground"
      )}
    >
      {children}
    </Link>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
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
    <div className="flex min-h-screen flex-col">
      <header className="border-b">
        <div className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between px-4">
          <div className="flex items-center gap-6">
            <Link href="/" className="text-sm font-semibold tracking-tight">
              PathAI
            </Link>
            <nav className="flex items-center gap-1">
              <NavLink
                href={`/dashboard/${runId}`}
                active={section === "dashboard" || section === "curriculum"}
              >
                Dashboard
              </NavLink>
              <NavLink href={`/orchestration/${runId}`} active={section === "orchestration"}>
                Orchestration
              </NavLink>
            </nav>
          </div>
          <ThemeToggle />
        </div>
      </header>
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">{children}</main>
    </div>
  );
}

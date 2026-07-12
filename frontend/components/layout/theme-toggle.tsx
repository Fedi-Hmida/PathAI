"use client";

import * as React from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

import { CollapsingLabel } from "@/components/layout/sidebar-primitives";
import { cn } from "@/lib/utils";

export function ThemeToggle({ open }: { open: boolean }) {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    // One-time mount flag to defer theme-dependent rendering until after
    // hydration (next-themes' documented fix for the server/client mismatch).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
  }, []);

  const rowClasses =
    "text-muted-foreground hover:bg-surface-sunken hover:text-foreground flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium";

  if (!mounted) {
    return (
      <div className={cn(rowClasses, "pointer-events-none opacity-50")}>
        <Sun className="size-4 flex-none" />
        <CollapsingLabel open={open}>Theme</CollapsingLabel>
      </div>
    );
  }

  const isDark = resolvedTheme === "dark";
  const label = isDark ? "Dark mode" : "Light mode";

  return (
    <button
      type="button"
      title={open ? undefined : label}
      aria-label={`Switch to ${isDark ? "light" : "dark"} mode`}
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className={rowClasses}
    >
      {isDark ? <Moon className="size-4 flex-none" /> : <Sun className="size-4 flex-none" />}
      <CollapsingLabel open={open}>{label}</CollapsingLabel>
    </button>
  );
}

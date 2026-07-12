"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

export const SIDEBAR_TRANSITION = "var(--duration-slow) var(--ease-standard)";

export function CollapsingLabel({ open, children }: { open: boolean; children: React.ReactNode }) {
  return (
    <span
      className={cn("overflow-hidden whitespace-nowrap", open ? "max-w-[160px] opacity-100" : "max-w-0 opacity-0")}
      style={{ transition: `max-width ${SIDEBAR_TRANSITION}, opacity ${SIDEBAR_TRANSITION}` }}
    >
      {children}
    </span>
  );
}

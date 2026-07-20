"use client";

import * as React from "react";
import { Eye, Flag, SquareCheck } from "lucide-react";

import {
  computeTopicTrailLayout,
  type TrailNodeLayout,
  type TrailTopicInput,
} from "@/components/progress/topic-trail-geometry";
import { cn } from "@/lib/utils";
import type { TopicProgressStatus } from "@/lib/types/progress";

const STATUS_COLOR: Record<TopicProgressStatus, string> = {
  not_started: "var(--text-tertiary)",
  in_progress: "var(--brand)",
  completed: "var(--success)",
  stuck: "var(--warning)",
  needs_review: "var(--danger)",
};

const STATUS_ICON: Partial<Record<TopicProgressStatus, typeof SquareCheck>> = {
  completed: SquareCheck,
  stuck: Flag,
  needs_review: Eye,
};

export interface TopicTrailProps {
  topics: TrailTopicInput[];
}

export function TopicTrail({ topics }: TopicTrailProps) {
  const layout = React.useMemo(() => computeTopicTrailLayout(topics), [topics]);

  if (layout.nodes.length === 0) {
    return null;
  }

  return (
    <div
      className="relative mx-auto max-w-full overflow-x-auto"
      style={{ width: layout.width, height: layout.height }}
    >
      <svg
        width={layout.width}
        height={layout.height}
        className="pointer-events-none absolute top-0 left-0"
        style={{ overflow: "visible" }}
      >
        <path
          d={layout.pathD}
          fill="none"
          stroke="var(--border)"
          strokeWidth={2}
          strokeDasharray="1 8"
          strokeLinecap="round"
        />
      </svg>
      {layout.nodes.map((node) => (
        <TrailNode key={node.topicId} node={node} />
      ))}
    </div>
  );
}

function TrailNode({ node }: { node: TrailNodeLayout }) {
  const [expanded, setExpanded] = React.useState(false);
  const color = STATUS_COLOR[node.status];
  const Icon = STATUS_ICON[node.status];
  const hasDetail =
    node.lastScore !== null || node.attemptCount > 0 || node.stuckCount > 0 || !!node.notes;

  return (
    <div
      className="absolute w-35"
      style={{ left: node.left, top: node.top }}
    >
      {node.isCurrent ? (
        <div
          className="absolute left-1/2 -top-6.5 -translate-x-1/2 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold tracking-wide whitespace-nowrap uppercase"
          style={{ color, borderColor: color, backgroundColor: "var(--card)" }}
        >
          You are here
        </div>
      ) : null}

      <button
        type="button"
        onClick={() => (hasDetail ? setExpanded((value) => !value) : undefined)}
        aria-expanded={expanded}
        className={cn(
          "relative mx-auto block rounded-full",
          node.status === "in_progress" ? "motion-safe:animate-pulse" : ""
        )}
        style={{ width: node.size, height: node.size }}
      >
        <svg
          width={node.size}
          height={node.size}
          viewBox={`0 0 ${node.size} ${node.size}`}
          style={{ transform: "rotate(-90deg)" }}
          className="absolute inset-0"
        >
          <circle
            cx={node.size / 2}
            cy={node.size / 2}
            r={node.radius}
            fill="var(--card)"
            stroke="var(--surface-sunken)"
            strokeWidth={node.stroke}
          />
          <circle
            cx={node.size / 2}
            cy={node.size / 2}
            r={node.radius}
            fill="none"
            stroke={color}
            strokeWidth={node.stroke}
            strokeLinecap="round"
            strokeDasharray={node.circumference}
            strokeDashoffset={node.offset}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          {Icon ? <Icon className="size-4" style={{ color }} /> : null}
        </div>

        {expanded ? (
          <div
            className={cn(
              "border-border bg-card absolute left-1/2 z-20 w-55 -translate-x-1/2 rounded-2xl border p-3.5 text-left shadow-lg",
              node.popoverPlacement === "bottom" ? "top-[calc(100%+10px)]" : "bottom-[calc(100%+10px)]"
            )}
          >
            <div className="text-foreground mb-1.5 text-sm font-semibold">{node.title}</div>
            {node.lastScore !== null && node.lastScore !== undefined ? (
              <div className="text-muted-foreground mb-1 font-mono text-xs">
                Last score {node.lastScore.toFixed(2)}
              </div>
            ) : null}
            {node.attemptCount > 0 ? (
              <div className="text-muted-foreground mb-1 text-xs">
                {node.attemptCount} attempt{node.attemptCount === 1 ? "" : "s"}
              </div>
            ) : null}
            {node.stuckCount > 0 ? (
              <div className="bg-warning-tint text-warning mb-1 inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold">
                {node.stuckCount} stuck event{node.stuckCount === 1 ? "" : "s"}
              </div>
            ) : null}
            {node.notes ? (
              <div className="text-muted-foreground mt-1 text-xs leading-relaxed">{node.notes}</div>
            ) : null}
          </div>
        ) : null}
      </button>

      <div className="text-foreground mt-2.5 text-center text-xs leading-snug font-medium">
        {node.title}
      </div>
    </div>
  );
}

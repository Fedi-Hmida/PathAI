"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

export type TrailStoneStatus = "completed" | "current" | "unknown";

export type TrailStone = {
  key: string;
  status: TrailStoneStatus;
  size: number;
  selected?: boolean;
  disabled?: boolean;
  title?: string;
  onClick?: () => void;
  content: React.ReactNode;
};

// Wave amplitude/frequency chosen to read as a gentle up-down-up path at
// any stone count, matching the curved trail from the approved curriculum
// screen mockup (straight-line connectors read as a plain progress bar).
const WAVE_AMPLITUDE = 28;
const WAVE_FREQUENCY = 2.15;

// Fixed so the wave's vertical swing (amplitude + largest stone's radius)
// never exceeds the container — sizing this from padding instead caused
// stones near the wave's peak to clip against overflow-y.
const CONTAINER_HEIGHT = 152;

// Minimum breathing room between stone edges when the row is wide enough
// to spread across the full container instead of overflowing it.
const MIN_GAP = 32;

export function waveOffset(index: number): number {
  return Math.round(Math.sin((index + 0.5) * WAVE_FREQUENCY) * WAVE_AMPLITUDE);
}

// Smooths a polyline into a single cubic-bezier path via Catmull-Rom
// control points, so the connector flows through every stone's center
// instead of joining them with straight segments.
function smoothPath(points: { x: number; y: number }[]): string {
  if (points.length === 0) {
    return "";
  }
  if (points.length === 1) {
    return `M ${points[0]!.x} ${points[0]!.y}`;
  }

  let d = `M ${points[0]!.x} ${points[0]!.y}`;
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i === 0 ? i : i - 1]!;
    const p1 = points[i]!;
    const p2 = points[i + 1]!;
    const p3 = points[i + 2 < points.length ? i + 2 : i + 1]!;
    const cp1x = p1.x + (p2.x - p0.x) / 6;
    const cp1y = p1.y + (p2.y - p0.y) / 6;
    const cp2x = p2.x - (p3.x - p1.x) / 6;
    const cp2y = p2.y - (p3.y - p1.y) / 6;
    d += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`;
  }
  return d;
}

type WavyTrailProps = {
  stones: TrailStone[];
};

export function WavyTrail({ stones }: WavyTrailProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const stoneRefs = React.useRef<Map<string, HTMLElement>>(new Map());
  const [path, setPath] = React.useState("");
  const [svgSize, setSvgSize] = React.useState({ width: 0, height: 0 });

  const recomputePath = React.useCallback(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }
    const containerRect = container.getBoundingClientRect();
    const points = stones
      .map((stone) => stoneRefs.current.get(stone.key))
      .filter((el): el is HTMLElement => el !== undefined)
      .map((el) => {
        const rect = el.getBoundingClientRect();
        return {
          x: rect.left + rect.width / 2 - containerRect.left + container.scrollLeft,
          y: rect.top + rect.height / 2 - containerRect.top,
        };
      });
    setSvgSize({ width: container.scrollWidth, height: containerRect.height });
    setPath(smoothPath(points));
  }, [stones]);

  React.useLayoutEffect(() => {
    recomputePath();
  }, [recomputePath]);

  React.useEffect(() => {
    const container = containerRef.current;
    if (!container || typeof ResizeObserver === "undefined") {
      return;
    }
    const observer = new ResizeObserver(recomputePath);
    observer.observe(container);
    return () => observer.disconnect();
  }, [recomputePath]);

  const minRowWidth =
    stones.reduce((sum, stone) => sum + stone.size, 0) + Math.max(stones.length - 1, 0) * MIN_GAP;

  return (
    <div
      ref={containerRef}
      className="relative overflow-x-auto px-4"
      style={{ height: CONTAINER_HEIGHT }}
    >
      <svg
        className="pointer-events-none absolute top-0 left-0"
        width={svgSize.width}
        height={svgSize.height}
      >
        <path d={path} fill="none" stroke="var(--color-border)" strokeWidth={2.5} />
      </svg>
      <div
        className="relative flex h-full w-full items-center justify-between"
        style={{ minWidth: minRowWidth }}
      >
        {stones.map((stone) => (
          <button
            key={stone.key}
            ref={(el) => {
              if (el) {
                stoneRefs.current.set(stone.key, el);
              } else {
                stoneRefs.current.delete(stone.key);
              }
            }}
            type="button"
            title={stone.title}
            disabled={stone.disabled}
            onClick={stone.onClick}
            style={{ width: stone.size, height: stone.size, transform: `translateY(${waveOffset(stones.indexOf(stone))}px)` }}
            className={cn(
              "relative z-10 flex flex-none items-center justify-center rounded-full transition-transform",
              stone.status === "completed" && "bg-success",
              stone.status === "current" && "bg-brand shadow-[0_0_0_6px_var(--brand-tint)]",
              stone.status === "unknown" && "border-border bg-card border-2",
              stone.selected && "ring-brand ring-offset-background ring-2 ring-offset-2",
              stone.disabled && "cursor-default opacity-60"
            )}
          >
            {stone.content}
          </button>
        ))}
      </div>
    </div>
  );
}

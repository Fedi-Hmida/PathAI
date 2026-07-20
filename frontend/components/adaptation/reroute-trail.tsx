import {
  computeRerouteTrailLayout,
  type ReroutePoint,
} from "@/components/adaptation/reroute-trail-geometry";

export interface RerouteTrailProps {
  weekNumbers: number[];
  targetWeeks: number[];
}

export function RerouteTrail({ weekNumbers, targetWeeks }: RerouteTrailProps) {
  const { pathD, points } = computeRerouteTrailLayout(weekNumbers);
  const targetSet = new Set(targetWeeks);

  if (points.length === 0) {
    return null;
  }

  return (
    <div className="grid grid-cols-2 gap-5">
      <TrailPanel title="Before" pathD={pathD} points={points} targetSet={null} />
      <TrailPanel title="After" pathD={pathD} points={points} targetSet={targetSet} />
    </div>
  );
}

function TrailPanel({
  title,
  pathD,
  points,
  targetSet,
}: {
  title: string;
  pathD: string;
  points: ReroutePoint[];
  targetSet: Set<number> | null;
}) {
  const sortedTargets = targetSet ? [...targetSet].sort((a, b) => a - b) : [];

  return (
    <div className="border-border bg-card rounded-2xl border p-5 shadow-sm">
      <div className="text-tertiary mb-2 text-[11px] font-semibold tracking-wide uppercase">
        {title}
      </div>
      <svg viewBox="0 0 400 110" className="block h-auto w-full">
        <path
          d={pathD}
          fill="none"
          stroke="var(--border)"
          strokeWidth={2}
          strokeDasharray="4 5"
          strokeLinecap="round"
        />
        {points.map((point) => {
          const isTarget = targetSet?.has(point.weekNumber) ?? false;
          return (
            <g key={point.weekNumber}>
              {isTarget ? (
                <circle
                  cx={point.x}
                  cy={point.y}
                  r={9}
                  fill="none"
                  stroke="var(--brand)"
                  strokeWidth={2}
                />
              ) : null}
              <circle
                cx={point.x}
                cy={point.y}
                r={9}
                fill={isTarget ? "var(--brand)" : "var(--surface-sunken)"}
                stroke={isTarget ? "var(--brand)" : "var(--border)"}
                strokeWidth={1.5}
              />
              <text
                x={point.x}
                y={point.textY}
                textAnchor="middle"
                fontFamily="var(--font-mono)"
                fontSize={9}
                fontWeight={isTarget ? 700 : 400}
                fill={isTarget ? "var(--brand)" : "var(--text-tertiary)"}
              >
                {point.weekNumber}
              </text>
            </g>
          );
        })}
      </svg>
      {sortedTargets.length > 0 ? (
        <div className="mt-1 flex flex-wrap gap-3.5">
          {sortedTargets.map((weekNumber) => (
            <span key={weekNumber} className="text-brand font-mono text-[10px] font-semibold">
              Week {weekNumber}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

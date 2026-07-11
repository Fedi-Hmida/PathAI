const DEFAULT_STROKE_WIDTH = 6;

type ProgressRingProps = {
  value: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
  hideLabel?: boolean;
  indicatorColor?: string;
};

export function ProgressRing({
  value,
  size = 72,
  strokeWidth = DEFAULT_STROKE_WIDTH,
  label = "complete",
  hideLabel = false,
  indicatorColor = "var(--primary)",
}: ProgressRingProps) {
  const clamped = Math.min(100, Math.max(0, value));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - clamped / 100);

  return (
    <div
      className="relative inline-flex flex-none items-center justify-center"
      style={{ width: size, height: size }}
      role="img"
      aria-label={`${clamped}% ${label}`}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--surface-sunken)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={indicatorColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset var(--duration-slow) var(--ease-standard)" }}
        />
      </svg>
      {hideLabel ? null : (
        <span className="font-tabular absolute text-sm font-semibold text-foreground">
          {clamped}%
        </span>
      )}
    </div>
  );
}

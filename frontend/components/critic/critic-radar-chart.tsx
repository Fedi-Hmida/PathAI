import { computeRadarGeometry, RADAR_TONE_COLOR } from "@/components/critic/radar-geometry";
import type { CriticDimensionScores } from "@/lib/types/critic";

const SIZE = 380;

export interface CriticRadarChartProps {
  dimensionScores: CriticDimensionScores;
  overallScore: number;
}

export function CriticRadarChart({ dimensionScores, overallScore }: CriticRadarChartProps) {
  const geometry = computeRadarGeometry(dimensionScores);
  const shapeColor = RADAR_TONE_COLOR[geometry.shapeTone];

  return (
    <svg
      width={SIZE}
      height={SIZE}
      viewBox={`0 0 ${SIZE} ${SIZE}`}
      style={{ overflow: "visible", maxWidth: "100%" }}
      role="img"
      aria-label="Critic review dimension scores"
    >
      {geometry.gridRings.map((points, index) => (
        <polygon key={index} points={points} fill="none" stroke="var(--border)" strokeWidth={1} />
      ))}
      {geometry.axes.map((axis) => (
        <line
          key={`grid-${axis.key}`}
          x1={geometry.cx}
          y1={geometry.cy}
          x2={axis.gridX}
          y2={axis.gridY}
          stroke="var(--border)"
          strokeWidth={1}
        />
      ))}
      <polygon
        points={geometry.dataPolygonPoints}
        fill={shapeColor}
        fillOpacity={0.16}
        stroke={shapeColor}
        strokeWidth={2}
      />
      {geometry.axes.map((axis) => {
        const color = RADAR_TONE_COLOR[axis.tone];
        return (
          <g key={axis.key}>
            <line
              x1={geometry.cx}
              y1={geometry.cy}
              x2={axis.vertexX}
              y2={axis.vertexY}
              stroke={color}
              strokeWidth={2.5}
              strokeLinecap="round"
              strokeDasharray={axis.dashed ? "4 4" : undefined}
            />
            <circle cx={axis.vertexX} cy={axis.vertexY} r={4} fill={color} />
            <text
              x={axis.labelX}
              y={axis.labelY}
              textAnchor={axis.anchor}
              dominantBaseline="middle"
              fill="var(--text-secondary)"
              className="text-[12.5px] font-semibold"
            >
              {axis.label}
            </text>
            <text
              x={axis.valueLabelX}
              y={axis.valueLabelY}
              textAnchor={axis.anchor}
              dominantBaseline="middle"
              fill={color}
              className="font-mono text-[11px] font-medium"
            >
              {axis.valueLabel}
            </text>
          </g>
        );
      })}
      <text
        x={geometry.cx}
        y={geometry.centerScoreY}
        textAnchor="middle"
        dominantBaseline="middle"
        fill="var(--foreground)"
        className="font-mono text-[22px] font-semibold"
      >
        {overallScore.toFixed(2)}
      </text>
      <text
        x={geometry.cx}
        y={geometry.centerLabelY}
        textAnchor="middle"
        dominantBaseline="middle"
        fill="var(--text-tertiary)"
        className="text-[10px] font-semibold tracking-widest uppercase"
      >
        Overall
      </text>
    </svg>
  );
}

import { scoreBand } from "@/lib/score-band";
import type { CriticDimensionScores } from "@/lib/types/critic";

const CX = 190;
const CY = 190;
const MAX_R = 130;
const LABEL_R = 160;
const GRID_RING_FRACTIONS = [0.2, 0.4, 0.6, 0.8, 1];

type DimensionKey = keyof CriticDimensionScores;

const AXIS_DEFS: { key: DimensionKey; label: string }[] = [
  { key: "coverage", label: "Coverage" },
  { key: "pacing", label: "Pacing" },
  { key: "resource_relevance", label: "Resource relevance" },
  { key: "assessment_alignment", label: "Assessment alignment" },
  { key: "quiz_readiness", label: "Quiz readiness" },
];

export type RadarTone = "success" | "brand" | "warning" | "neutral";

export const RADAR_TONE_COLOR: Record<RadarTone, string> = {
  success: "var(--success)",
  brand: "var(--brand)",
  warning: "var(--warning)",
  neutral: "var(--text-tertiary)",
};

export type RadarAxis = {
  key: DimensionKey;
  label: string;
  valueLabel: string;
  tone: RadarTone;
  dashed: boolean;
  gridX: number;
  gridY: number;
  vertexX: number;
  vertexY: number;
  labelX: number;
  labelY: number;
  valueLabelX: number;
  valueLabelY: number;
  anchor: "start" | "end" | "middle";
};

export type RadarGeometry = {
  cx: number;
  cy: number;
  centerScoreY: number;
  centerLabelY: number;
  axes: RadarAxis[];
  gridRings: string[];
  dataPolygonPoints: string;
  shapeTone: RadarTone;
};

function axisAngleRadians(index: number): number {
  return ((-90 + index * 72) * Math.PI) / 180;
}

export function computeRadarGeometry(dimensionScores: CriticDimensionScores): RadarGeometry {
  const axes = AXIS_DEFS.map((def, index) => {
    const angle = axisAngleRadians(index);
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);
    const value = dimensionScores[def.key];
    const isNull = value === null;
    const radius = isNull ? 0 : value * MAX_R;
    const anchor: RadarAxis["anchor"] = cos > 0.25 ? "start" : cos < -0.25 ? "end" : "middle";

    return {
      key: def.key,
      label: def.label,
      valueLabel: isNull ? "Not yet scored" : value.toFixed(2),
      tone: isNull ? "neutral" : scoreBand(value),
      dashed: isNull,
      gridX: CX + MAX_R * cos,
      gridY: CY + MAX_R * sin,
      vertexX: CX + radius * cos,
      vertexY: CY + radius * sin,
      labelX: CX + LABEL_R * cos,
      labelY: CY + LABEL_R * sin,
      valueLabelX: CX + (radius + 16) * cos,
      valueLabelY: CY + (radius + 16) * sin,
      anchor,
    } satisfies RadarAxis;
  });

  const numericValues = AXIS_DEFS.map((def) => dimensionScores[def.key]).filter(
    (value): value is number => value !== null
  );
  const lowest = numericValues.length > 0 ? Math.min(...numericValues) : null;
  const shapeTone: RadarTone = lowest === null ? "neutral" : scoreBand(lowest);

  const gridRings = GRID_RING_FRACTIONS.map((fraction) =>
    AXIS_DEFS.map((_, index) => {
      const angle = axisAngleRadians(index);
      const x = CX + MAX_R * fraction * Math.cos(angle);
      const y = CY + MAX_R * fraction * Math.sin(angle);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(" ")
  );

  const dataPolygonPoints = axes
    .map((axis) => `${axis.vertexX.toFixed(1)},${axis.vertexY.toFixed(1)}`)
    .join(" ");

  return {
    cx: CX,
    cy: CY,
    centerScoreY: CY - 4,
    centerLabelY: CY + 14,
    axes,
    gridRings,
    dataPolygonPoints,
    shapeTone,
  };
}

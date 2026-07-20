const X_STEP = 68;
const X_START = 30;
const Y_CENTER = 55;
const Y_AMPLITUDE = 26;

export type ReroutePoint = {
  weekNumber: number;
  x: number;
  y: number;
  textY: number;
};

export type ReroutTrailLayout = {
  pathD: string;
  points: ReroutePoint[];
};

export function computeRerouteTrailLayout(weekNumbers: number[]): ReroutTrailLayout {
  const points: ReroutePoint[] = weekNumbers.map((weekNumber, i) => {
    const x = X_START + i * X_STEP;
    const y = Math.round(Y_CENTER + Math.sin(i * 1.05 + 0.4) * Y_AMPLITUDE);
    return { weekNumber, x, y, textY: y + 22 };
  });

  const pathD = points.length > 0 ? `M ${points.map((p) => `${p.x} ${p.y}`).join(" L ")}` : "";

  return { pathD, points };
}

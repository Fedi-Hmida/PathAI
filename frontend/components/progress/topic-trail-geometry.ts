import type { TopicProgressStatus } from "@/lib/types/progress";

const WIDTH = 900;
const BOX_WIDTH = 140;
// Wide enough that a centered 220px-wide node popover never clips past the
// scroll container's edge (110px half-width + a small buffer).
const PAD_X = 114;
const PAD_Y = 70;
const ROW_HEIGHT = 172;
const CURRENT_SIZE = 104;
const DEFAULT_SIZE = 76;
const CURRENT_STROKE = 9;
const DEFAULT_STROKE = 7;

export type TrailTopicInput = {
  topicId: string;
  title: string;
  status: TopicProgressStatus;
  completion: number;
  isCurrent: boolean;
  lastScore: number | null;
  attemptCount: number;
  stuckCount: number;
  notes: string | null;
};

export type TrailNodeLayout = TrailTopicInput & {
  left: number;
  top: number;
  size: number;
  stroke: number;
  radius: number;
  circumference: number;
  offset: number;
  popoverPlacement: "top" | "bottom";
};

export type TrailLayout = {
  width: number;
  height: number;
  pathD: string;
  nodes: TrailNodeLayout[];
};

export function computeTopicTrailLayout(topics: TrailTopicInput[]): TrailLayout {
  const n = topics.length;
  if (n === 0) {
    return { width: WIDTH, height: 0, pathD: "", nodes: [] };
  }

  const rows = n <= 6 ? 2 : 3;
  const perRow = Math.ceil(n / rows);
  const spacing = perRow > 1 ? (WIDTH - PAD_X * 2) / (perRow - 1) : 0;
  const height = PAD_Y * 2 + (rows - 1) * ROW_HEIGHT + 40;

  const centers = topics.map((_, i) => {
    const row = Math.floor(i / perRow);
    const posInRow = i % perRow;
    const x =
      row % 2 === 0 ? PAD_X + posInRow * spacing : PAD_X + (perRow - 1 - posInRow) * spacing;
    const y = PAD_Y + row * ROW_HEIGHT;
    return { x, y, row };
  });

  const nodes: TrailNodeLayout[] = topics.map((topic, i) => {
    const size = topic.isCurrent ? CURRENT_SIZE : DEFAULT_SIZE;
    const stroke = topic.isCurrent ? CURRENT_STROKE : DEFAULT_STROKE;
    const radius = (size - stroke) / 2;
    const circumference = 2 * Math.PI * radius;
    const hollow = topic.status === "not_started";
    const offset = hollow ? circumference : circumference - topic.completion * circumference;
    const center = centers[i]!;
    return {
      ...topic,
      left: center.x - BOX_WIDTH / 2,
      top: center.y - size / 2 - 10,
      size,
      stroke,
      radius,
      circumference,
      offset,
      popoverPlacement: center.row < rows - 1 ? "bottom" : "top",
    };
  });

  let pathD = "";
  const first = centers[0];
  if (first) {
    pathD = `M ${first.x} ${first.y}`;
    for (let i = 1; i < centers.length; i++) {
      const p0 = centers[i - 1]!;
      const p1 = centers[i]!;
      const dx = p1.x - p0.x;
      const wobble = i % 2 === 0 ? 20 : -20;
      const c1x = p0.x + dx * 0.5;
      const c1y = p0.y + wobble;
      const c2x = p1.x - dx * 0.5;
      const c2y = p1.y - wobble;
      pathD += ` C ${c1x} ${c1y}, ${c2x} ${c2y}, ${p1.x} ${p1.y}`;
    }
  }

  return { width: WIDTH, height, pathD, nodes };
}

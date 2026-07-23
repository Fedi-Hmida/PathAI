import { describe, expect, it } from "vitest";

import { computeRadarGeometry } from "@/components/critic/radar-geometry";
import type { CriticDimensionScores } from "@/lib/types/critic";

const CX = 190;
const CY = 190;

function scores(overrides: Partial<CriticDimensionScores> = {}): CriticDimensionScores {
  return {
    coverage: 0.9,
    pacing: 0.9,
    resource_relevance: 0.9,
    assessment_alignment: 0.9,
    quiz_readiness: 0.9,
    ...overrides,
  };
}

describe("computeRadarGeometry", () => {
  it("produces one axis per dimension, centered on (cx, cy)", () => {
    const geometry = computeRadarGeometry(scores());
    expect(geometry.cx).toBe(CX);
    expect(geometry.cy).toBe(CY);
    expect(geometry.axes).toHaveLength(5);
  });

  it("colors a scored axis by its own score band, not dashed", () => {
    const geometry = computeRadarGeometry(scores({ coverage: 0.9, pacing: 0.5 }));
    const coverage = geometry.axes.find((axis) => axis.key === "coverage")!;
    const pacing = geometry.axes.find((axis) => axis.key === "pacing")!;

    expect(coverage.tone).toBe("success");
    expect(coverage.dashed).toBe(false);
    expect(coverage.valueLabel).toBe("0.90");

    expect(pacing.tone).toBe("warning");
    expect(pacing.dashed).toBe(false);
  });

  it("renders a null dimension as a dashed, neutral, zero-radius axis pinned to the center", () => {
    const geometry = computeRadarGeometry(scores({ quiz_readiness: null }));
    const quizReadiness = geometry.axes.find((axis) => axis.key === "quiz_readiness")!;

    expect(quizReadiness.dashed).toBe(true);
    expect(quizReadiness.tone).toBe("neutral");
    expect(quizReadiness.valueLabel).toBe("Not yet scored");
    expect(quizReadiness.vertexX).toBeCloseTo(CX);
    expect(quizReadiness.vertexY).toBeCloseTo(CY);
  });

  it("derives the overall shape tone from the single lowest scored dimension, ignoring nulls", () => {
    const geometry = computeRadarGeometry(
      scores({ coverage: 0.95, pacing: 0.55, quiz_readiness: null }),
    );
    // Lowest real score is 0.55 -> warning band, even though most axes are high.
    expect(geometry.shapeTone).toBe("warning");
  });

  it("falls back to a neutral shape tone when every dimension is null", () => {
    const geometry = computeRadarGeometry({
      coverage: null as unknown as number,
      pacing: null as unknown as number,
      resource_relevance: null as unknown as number,
      assessment_alignment: null as unknown as number,
      quiz_readiness: null,
    });
    expect(geometry.shapeTone).toBe("neutral");
  });
});

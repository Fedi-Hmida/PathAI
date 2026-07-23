import { describe, expect, it } from "vitest";

import { computeGraphLayout, curvedEdgePath } from "@/components/knowledge-map/graph-layout";
import type { ConceptMasteryDTO } from "@/lib/types/knowledge-map";

function concept(overrides: Partial<ConceptMasteryDTO> & { concept_id: string }): ConceptMasteryDTO {
  return {
    label: overrides.concept_id,
    mastery_score: 0.5,
    classification: "developing",
    evidence: [],
    prerequisites: [],
    recommended_action: null,
    confidence: null,
    ...overrides,
  };
}

describe("computeGraphLayout", () => {
  it("puts a root concept (no prerequisites) in layer 0", () => {
    const layout = computeGraphLayout([concept({ concept_id: "a" })]);
    expect(layout.nodes).toHaveLength(1);
    expect(layout.nodes[0]!.layer).toBe(0);
    expect(layout.edges).toHaveLength(0);
  });

  it("places a concept one layer past its deepest prerequisite chain", () => {
    // a -> b -> c: c depends on b, b depends on a.
    const layout = computeGraphLayout([
      concept({ concept_id: "a" }),
      concept({ concept_id: "b", prerequisites: ["a"] }),
      concept({ concept_id: "c", prerequisites: ["b"] }),
    ]);
    const byId = new Map(layout.nodes.map((node) => [node.conceptId, node]));
    expect(byId.get("a")!.layer).toBe(0);
    expect(byId.get("b")!.layer).toBe(1);
    expect(byId.get("c")!.layer).toBe(2);
  });

  it("takes the longest path when a concept has multiple prerequisites at different depths", () => {
    // d depends on both a (layer 0) and c (layer 2, since c depends on b
    // which depends on a) - d must land one past the deepest prerequisite
    // (layer 3), not one past the shallowest (layer 1).
    const layout = computeGraphLayout([
      concept({ concept_id: "a" }),
      concept({ concept_id: "b", prerequisites: ["a"] }),
      concept({ concept_id: "c", prerequisites: ["b"] }),
      concept({ concept_id: "d", prerequisites: ["a", "c"] }),
    ]);
    const byId = new Map(layout.nodes.map((node) => [node.conceptId, node]));
    expect(byId.get("d")!.layer).toBe(3);
  });

  it("ignores a prerequisite id that isn't in the concept set (never crashes or fabricates a node)", () => {
    const layout = computeGraphLayout([
      concept({ concept_id: "a", prerequisites: ["missing_concept"] }),
    ]);
    expect(layout.nodes).toHaveLength(1);
    expect(layout.nodes[0]!.layer).toBe(0);
    expect(layout.edges).toHaveLength(0);
  });

  it("breaks a prerequisite cycle instead of recursing forever", () => {
    // a depends on b, b depends on a - a genuinely malformed knowledge map
    // the layout must still terminate and produce a layer for both.
    const layout = computeGraphLayout([
      concept({ concept_id: "a", prerequisites: ["b"] }),
      concept({ concept_id: "b", prerequisites: ["a"] }),
    ]);
    expect(layout.nodes).toHaveLength(2);
    for (const node of layout.nodes) {
      expect(Number.isFinite(node.layer)).toBe(true);
    }
  });

  it("produces one edge per known prerequisite relationship, pointing prerequisite -> dependent", () => {
    const layout = computeGraphLayout([
      concept({ concept_id: "a" }),
      concept({ concept_id: "b", prerequisites: ["a"] }),
    ]);
    expect(layout.edges).toEqual([{ fromConceptId: "a", toConceptId: "b" }]);
  });
});

describe("curvedEdgePath", () => {
  it("starts and ends exactly at the two node centers", () => {
    const path = curvedEdgePath(0, 0, 300, 150);
    expect(path.startsWith("M 0 0 C")).toBe(true);
    expect(path.endsWith("300 150")).toBe(true);
  });

  it("keeps a minimum horizontal control-point offset for vertically stacked nodes", () => {
    // x1 === x2 means the naive offset (dx = |x2-x1|*0.5) would be 0, which
    // would collapse the curve into a straight vertical line.
    const path = curvedEdgePath(100, 0, 100, 300);
    expect(path).toContain("140");
    expect(path).toContain("60");
  });
});

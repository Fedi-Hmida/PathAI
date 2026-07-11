import type { ConceptMasteryDTO } from "@/lib/types/knowledge-map";

const LAYER_SPACING_X = 210;
const NODE_SPACING_Y = 150;
const CANVAS_PADDING = 80;

export type GraphNode = {
  conceptId: string;
  x: number;
  y: number;
  layer: number;
};

export type GraphEdge = {
  fromConceptId: string;
  toConceptId: string;
};

export type GraphLayout = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  width: number;
  height: number;
};

function computeLayers(concepts: ConceptMasteryDTO[]): Map<string, number> {
  const conceptById = new Map(concepts.map((concept) => [concept.concept_id, concept]));
  const layers = new Map<string, number>();
  const visiting = new Set<string>();

  function layerOf(conceptId: string): number {
    const cached = layers.get(conceptId);
    if (cached !== undefined) {
      return cached;
    }
    if (visiting.has(conceptId)) {
      return 0;
    }
    visiting.add(conceptId);

    const concept = conceptById.get(conceptId);
    const knownPrerequisites = (concept?.prerequisites ?? []).filter((id) => conceptById.has(id));
    const layer =
      knownPrerequisites.length === 0
        ? 0
        : 1 + Math.max(...knownPrerequisites.map((id) => layerOf(id)));

    visiting.delete(conceptId);
    layers.set(conceptId, layer);
    return layer;
  }

  for (const concept of concepts) {
    layerOf(concept.concept_id);
  }
  return layers;
}

export function computeGraphLayout(concepts: ConceptMasteryDTO[]): GraphLayout {
  const conceptById = new Map(concepts.map((concept) => [concept.concept_id, concept]));
  const layers = computeLayers(concepts);

  // Flow is left → right: each prerequisite depth becomes a column, and the
  // concepts within a column are stacked vertically. Roots (no prerequisites)
  // sit on the left, the most-dependent concepts on the right — matching the
  // approved knowledge-map mockup.
  const nodesByLayer = new Map<number, string[]>();
  for (const concept of concepts) {
    const layer = layers.get(concept.concept_id) ?? 0;
    const bucket = nodesByLayer.get(layer) ?? [];
    bucket.push(concept.concept_id);
    nodesByLayer.set(layer, bucket);
  }

  const maxLayer = Math.max(0, ...nodesByLayer.keys());
  const maxNodesInLayer = Math.max(1, ...Array.from(nodesByLayer.values(), (ids) => ids.length));
  const width = (maxLayer + 1) * LAYER_SPACING_X + CANVAS_PADDING * 2;
  const height = maxNodesInLayer * NODE_SPACING_Y + CANVAS_PADDING * 2;

  const positions = new Map<string, { x: number; y: number }>();
  for (const [layer, ids] of nodesByLayer) {
    const columnHeight = ids.length * NODE_SPACING_Y;
    const startY = (height - columnHeight) / 2 + NODE_SPACING_Y / 2;
    ids.forEach((conceptId, index) => {
      positions.set(conceptId, {
        x: CANVAS_PADDING + layer * LAYER_SPACING_X + LAYER_SPACING_X / 2,
        y: startY + index * NODE_SPACING_Y,
      });
    });
  }

  const nodes: GraphNode[] = concepts.map((concept) => {
    const position = positions.get(concept.concept_id)!;
    return {
      conceptId: concept.concept_id,
      x: position.x,
      y: position.y,
      layer: layers.get(concept.concept_id) ?? 0,
    };
  });

  const edges: GraphEdge[] = [];
  for (const concept of concepts) {
    for (const prerequisiteId of concept.prerequisites) {
      if (conceptById.has(prerequisiteId)) {
        edges.push({ fromConceptId: prerequisiteId, toConceptId: concept.concept_id });
      }
    }
  }

  return { nodes, edges, width, height };
}

// Smooth left→right connector between two node centers: a cubic bézier whose
// control points are offset horizontally, giving the gentle S-curve from the
// mockup instead of a straight segment.
export function curvedEdgePath(x1: number, y1: number, x2: number, y2: number): string {
  const dx = Math.max(Math.abs(x2 - x1) * 0.5, 40);
  return `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;
}

import type { ConceptMasteryDTO } from "@/lib/types/knowledge-map";

const NODE_SPACING_X = 170;
const LAYER_HEIGHT = 170;
const CANVAS_PADDING = 70;

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

  const nodesByLayer = new Map<number, string[]>();
  for (const concept of concepts) {
    const layer = layers.get(concept.concept_id) ?? 0;
    const bucket = nodesByLayer.get(layer) ?? [];
    bucket.push(concept.concept_id);
    nodesByLayer.set(layer, bucket);
  }

  const maxLayer = Math.max(0, ...nodesByLayer.keys());
  const maxNodesInLayer = Math.max(1, ...Array.from(nodesByLayer.values(), (ids) => ids.length));
  const width = maxNodesInLayer * NODE_SPACING_X + CANVAS_PADDING * 2;
  const height = (maxLayer + 1) * LAYER_HEIGHT + CANVAS_PADDING * 2;

  const positions = new Map<string, { x: number; y: number }>();
  for (const [layer, ids] of nodesByLayer) {
    const rowWidth = ids.length * NODE_SPACING_X;
    const startX = (width - rowWidth) / 2 + NODE_SPACING_X / 2;
    ids.forEach((conceptId, index) => {
      positions.set(conceptId, {
        x: startX + index * NODE_SPACING_X,
        y: CANVAS_PADDING + layer * LAYER_HEIGHT + LAYER_HEIGHT / 2,
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

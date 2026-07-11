"use client";

import * as React from "react";
import { Minus, Plus, RotateCcw, Search } from "lucide-react";

import { ConceptNode } from "@/components/knowledge-map/concept-node";
import { CLASSIFICATION_CONFIG, ClassificationLegend } from "@/components/knowledge-map/classification-legend";
import { computeGraphLayout, curvedEdgePath } from "@/components/knowledge-map/graph-layout";
import { cn } from "@/lib/utils";
import type { ConceptClassification, ConceptMasteryDTO } from "@/lib/types/knowledge-map";

const MIN_SCALE = 0.5;
const MAX_SCALE = 2;
const ZOOM_STEP = 0.2;
const CANVAS_HEIGHT = 480;

type ConceptGraphProps = {
  concepts: ConceptMasteryDTO[];
  selectedConceptId: string;
  onSelectConcept: (conceptId: string) => void;
};

export function ConceptGraph({ concepts, selectedConceptId, onSelectConcept }: ConceptGraphProps) {
  const layout = React.useMemo(() => computeGraphLayout(concepts), [concepts]);
  const nodesByConceptId = React.useMemo(
    () => new Map(layout.nodes.map((node) => [node.conceptId, node])),
    [layout.nodes]
  );
  const conceptsById = React.useMemo(
    () => new Map(concepts.map((concept) => [concept.concept_id, concept])),
    [concepts]
  );

  const [pan, setPan] = React.useState({ x: 0, y: 0 });
  const [scale, setScale] = React.useState(1);
  const [searchText, setSearchText] = React.useState("");
  const [activeClassifications, setActiveClassifications] = React.useState<
    Set<ConceptClassification>
  >(new Set(["strong", "developing", "weak", "missing"]));

  const dragState = React.useRef<{ startX: number; startY: number; originX: number; originY: number } | null>(
    null
  );
  const [isDragging, setIsDragging] = React.useState(false);
  const canvasRef = React.useRef<HTMLDivElement>(null);

  // React's synthetic onWheel is attached passively, so preventDefault()
  // there only warns without stopping page scroll. A native listener with
  // { passive: false } is required to actually capture the zoom gesture.
  React.useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      setScale((value) => Math.min(MAX_SCALE, Math.max(MIN_SCALE, value - event.deltaY * 0.001)));
    };
    canvas.addEventListener("wheel", onWheel, { passive: false });
    return () => canvas.removeEventListener("wheel", onWheel);
  }, []);

  // Fit the whole graph inside the visible canvas: scale it down (or up, to a
  // cap) so the full DAG is framed with a little margin, then centre it. This
  // is what keeps a small map from floating as tiny nodes in a big void.
  const fitView = React.useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || layout.width === 0 || layout.height === 0) {
      return;
    }
    const margin = 32;
    const availableWidth = canvas.clientWidth - margin * 2;
    const availableHeight = canvas.clientHeight - margin * 2;
    const nextScale = Math.min(
      MAX_SCALE,
      Math.max(MIN_SCALE, Math.min(availableWidth / layout.width, availableHeight / layout.height))
    );
    setScale(nextScale);
    setPan({
      x: (canvas.clientWidth - layout.width * nextScale) / 2,
      y: (canvas.clientHeight - layout.height * nextScale) / 2,
    });
  }, [layout.width, layout.height]);

  // Frame on first paint and whenever the layout changes.
  React.useLayoutEffect(() => {
    fitView();
  }, [fitView]);

  const handlePointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
    // Don't start a pan (and don't steal pointer capture) when the
    // gesture starts on a node or a toolbar control — otherwise the
    // captured pointer suppresses the child button's click event.
    if ((event.target as HTMLElement).closest("button")) {
      return;
    }
    dragState.current = {
      startX: event.clientX,
      startY: event.clientY,
      originX: pan.x,
      originY: pan.y,
    };
    setIsDragging(true);
    event.currentTarget.setPointerCapture(event.pointerId);
  };

  const handlePointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    if (!dragState.current) {
      return;
    }
    const dx = event.clientX - dragState.current.startX;
    const dy = event.clientY - dragState.current.startY;
    setPan({ x: dragState.current.originX + dx, y: dragState.current.originY + dy });
  };

  const handlePointerUp = () => {
    dragState.current = null;
    setIsDragging(false);
  };

  const handleReset = () => {
    fitView();
  };

  const toggleClassification = (classification: ConceptClassification) => {
    setActiveClassifications((prev) => {
      const next = new Set(prev);
      if (next.has(classification)) {
        next.delete(classification);
      } else {
        next.add(classification);
      }
      return next;
    });
  };

  const normalizedSearch = searchText.trim().toLowerCase();

  const isDimmed = (concept: ConceptMasteryDTO) => {
    if (!activeClassifications.has(concept.classification)) {
      return true;
    }
    if (normalizedSearch.length > 0 && !concept.label.toLowerCase().includes(normalizedSearch)) {
      return true;
    }
    return false;
  };

  return (
    <div className="border-border bg-card flex-[2_1_520px] overflow-hidden rounded-2xl border shadow-sm">
      <div className="border-border flex flex-wrap items-center justify-between gap-3 border-b px-5 py-3.5">
        <ClassificationLegend
          concepts={concepts}
          activeClassifications={activeClassifications}
          onToggleClassification={toggleClassification}
        />
        <div className="flex items-center gap-2">
          <div className="border-border bg-background flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5">
            <Search className="text-tertiary size-3.5 flex-none" />
            <input
              type="text"
              value={searchText}
              onChange={(event) => setSearchText(event.target.value)}
              placeholder="Search concepts"
              className="text-foreground placeholder:text-tertiary w-32 bg-transparent text-[13px] outline-none"
            />
          </div>
          <div className="border-border flex items-center gap-0.5 rounded-lg border p-0.5">
            <button
              type="button"
              onClick={() => setScale((value) => Math.max(MIN_SCALE, value - ZOOM_STEP))}
              aria-label="Zoom out"
              className="text-muted-foreground hover:bg-surface-sunken rounded-md p-1.5"
            >
              <Minus className="size-3.5" />
            </button>
            <button
              type="button"
              onClick={() => setScale((value) => Math.min(MAX_SCALE, value + ZOOM_STEP))}
              aria-label="Zoom in"
              className="text-muted-foreground hover:bg-surface-sunken rounded-md p-1.5"
            >
              <Plus className="size-3.5" />
            </button>
            <button
              type="button"
              onClick={handleReset}
              aria-label="Reset view"
              className="text-muted-foreground hover:bg-surface-sunken rounded-md p-1.5"
            >
              <RotateCcw className="size-3.5" />
            </button>
          </div>
        </div>
      </div>

      <div
        ref={canvasRef}
        className={cn(
          "relative overflow-hidden",
          isDragging ? "cursor-grabbing" : "cursor-grab"
        )}
        style={{ height: CANVAS_HEIGHT }}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerLeave={handlePointerUp}
      >
        <div
          className="absolute top-0 left-0"
          style={{
            width: layout.width,
            height: layout.height,
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale})`,
            transformOrigin: "0 0",
          }}
        >
          <svg
            className="pointer-events-none absolute top-0 left-0"
            width={layout.width}
            height={layout.height}
          >
            {layout.edges.map((edge) => {
              const from = nodesByConceptId.get(edge.fromConceptId);
              const to = nodesByConceptId.get(edge.toConceptId);
              if (!from || !to) {
                return null;
              }
              // Colour each connector by its source (prerequisite) concept's
              // classification, so the flow reads as "mastery feeding forward"
              // — matching the mockup's tinted edges.
              const source = conceptsById.get(edge.fromConceptId);
              const stroke = source
                ? CLASSIFICATION_CONFIG[source.classification].ringColor
                : "var(--color-border)";
              return (
                <path
                  key={`${edge.fromConceptId}-${edge.toConceptId}`}
                  d={curvedEdgePath(from.x, from.y, to.x, to.y)}
                  fill="none"
                  stroke={stroke}
                  strokeWidth={2}
                  strokeOpacity={0.55}
                />
              );
            })}
          </svg>

          {concepts.map((concept) => {
            const position = nodesByConceptId.get(concept.concept_id);
            if (!position) {
              return null;
            }
            return (
              <ConceptNode
                key={concept.concept_id}
                concept={concept}
                position={position}
                selected={concept.concept_id === selectedConceptId}
                dimmed={isDimmed(concept)}
                onSelect={onSelectConcept}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}

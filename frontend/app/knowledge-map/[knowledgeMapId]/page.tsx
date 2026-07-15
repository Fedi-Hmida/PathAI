"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, usePathname, useRouter, useSearchParams } from "next/navigation";
import { AlertTriangle, ArrowLeft } from "lucide-react";

import { RequireAuth } from "@/components/auth/require-auth";
import { ConceptDetailPanel } from "@/components/knowledge-map/concept-detail-panel";
import { ConceptGraph } from "@/components/knowledge-map/concept-graph";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/client";
import { getGoal } from "@/lib/api/goal";
import { getKnowledgeMap } from "@/lib/api/knowledge-map";
import { cn } from "@/lib/utils";
import type { KnowledgeMapDTO, KnowledgeMapStatus } from "@/lib/types/knowledge-map";

type KnowledgeMapLoadState =
  | { kind: "loading" }
  | { kind: "not_found" }
  | { kind: "invalid_id" }
  | { kind: "generation_unavailable" }
  | { kind: "ready"; knowledgeMap: KnowledgeMapDTO }
  | { kind: "error"; message: string };

const STATUS_CONFIG: Record<KnowledgeMapStatus, { label: string; className: string }> = {
  draft: { label: "Draft", className: "bg-surface-sunken text-tertiary" },
  active: { label: "Active", className: "bg-success-tint text-success" },
  superseded: { label: "Superseded", className: "bg-surface-sunken text-tertiary" },
  failed: { label: "Failed", className: "bg-danger-tint text-danger" },
};

export default function KnowledgeMapPage() {
  return (
    <RequireAuth>
      <React.Suspense fallback={<KnowledgeMapSkeleton />}>
        <KnowledgeMapView />
      </React.Suspense>
    </RequireAuth>
  );
}

function KnowledgeMapView() {
  const params = useParams<{ knowledgeMapId: string }>();
  const knowledgeMapId = params.knowledgeMapId;
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();

  const conceptParam = searchParams.get("concept");

  const [loadedKnowledgeMapId, setLoadedKnowledgeMapId] = React.useState(knowledgeMapId);
  const [state, setState] = React.useState<KnowledgeMapLoadState>({ kind: "loading" });
  const [goalText, setGoalText] = React.useState<string | null>(null);
  const [reloadNonce, setReloadNonce] = React.useState(0);

  if (knowledgeMapId !== loadedKnowledgeMapId) {
    setLoadedKnowledgeMapId(knowledgeMapId);
    setState({ kind: "loading" });
    setGoalText(null);
  }

  const retry = React.useCallback(() => {
    setState({ kind: "loading" });
    setReloadNonce((nonce) => nonce + 1);
  }, []);

  React.useEffect(() => {
    let cancelled = false;

    getKnowledgeMap(knowledgeMapId)
      .then((knowledgeMap) => {
        if (!cancelled) {
          setState({ kind: "ready", knowledgeMap });
        }
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        if (error instanceof ApiError && error.status === 404) {
          setState({ kind: "not_found" });
          return;
        }
        // The map couldn't be generated (LLM unavailable): show an honest
        // retry panel rather than falling through to placeholder content.
        if (error instanceof ApiError && error.code === "generation_unavailable") {
          setState({ kind: "generation_unavailable" });
          return;
        }
        // KnowledgeMapId requires a "kmap_" prefix + pattern
        // (schemas/ids.py); a malformed id fails FastAPI's request
        // validation with 422 before reaching the not-found path.
        if (error instanceof ApiError && error.status === 422) {
          setState({ kind: "invalid_id" });
          return;
        }
        const message =
          error instanceof ApiError ? error.message : "Unable to reach the PathAI backend.";
        setState({ kind: "error", message });
      });

    return () => {
      cancelled = true;
    };
  }, [knowledgeMapId, reloadNonce]);

  // The knowledge map carries the goal_id but not the goal text; fetch it for
  // the header title once the map has loaded, degrading to nothing (title
  // omitted) if the goal can't be fetched.
  const goalId = state.kind === "ready" ? state.knowledgeMap.goal_id : null;
  React.useEffect(() => {
    if (goalId === null) {
      return;
    }
    let cancelled = false;
    getGoal(goalId)
      .then((goal) => {
        if (!cancelled) {
          setGoalText(goal.goal_text);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setGoalText(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [goalId]);

  const navigateToConcept = React.useCallback(
    (conceptId: string) => {
      const next = new URLSearchParams(searchParams.toString());
      next.set("concept", conceptId);
      router.replace(`${pathname}?${next.toString()}`, { scroll: false });
    },
    [pathname, router, searchParams]
  );

  if (state.kind === "loading") {
    return <KnowledgeMapSkeleton />;
  }

  if (state.kind === "error") {
    return (
      <Alert variant="destructive">
        <AlertTitle>Couldn&apos;t load this knowledge map</AlertTitle>
        <AlertDescription>{state.message}</AlertDescription>
      </Alert>
    );
  }

  if (state.kind === "invalid_id") {
    return (
      <p className="text-muted-foreground text-sm">
        That doesn&apos;t look like a valid knowledge map ID.
      </p>
    );
  }

  if (state.kind === "generation_unavailable") {
    return (
      <Alert variant="destructive">
        <AlertTitle>We couldn&apos;t generate your knowledge map yet</AlertTitle>
        <AlertDescription className="flex flex-col items-start gap-3">
          <span>Generation didn&apos;t go through. Please retry.</span>
          <Button variant="outline" size="sm" onClick={retry}>
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  if (state.kind === "not_found") {
    return <p className="text-muted-foreground text-sm">Knowledge map not found.</p>;
  }

  const { knowledgeMap } = state;
  const status = STATUS_CONFIG[knowledgeMap.status];
  const conceptsById = new Map(knowledgeMap.concepts.map((concept) => [concept.concept_id, concept]));
  const selectedConcept =
    (conceptParam ? conceptsById.get(conceptParam) : undefined) ?? knowledgeMap.concepts[0]!;

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex min-w-0 items-start gap-3">
          <Link
            href={`/dashboard/${knowledgeMap.run_id}`}
            aria-label="Back to dashboard"
            className="border-border text-muted-foreground hover:bg-surface-sunken hover:text-foreground mt-0.5 flex size-9 flex-none items-center justify-center rounded-full border"
          >
            <ArrowLeft className="size-4" />
          </Link>
          <div className="min-w-0">
            <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
              Knowledge map
            </span>
            {goalText ? (
              <h1 className="font-goal text-foreground mt-0.5 text-2xl leading-tight font-medium italic">
                {goalText}
              </h1>
            ) : (
              <h1 className="font-goal text-foreground mt-0.5 text-2xl leading-tight font-medium">
                Concept Map
              </h1>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-tertiary font-mono text-[13px]">
            {Math.round(knowledgeMap.confidence * 100)}% confidence
          </span>
          <Badge className={cn("rounded-full px-3 py-1.5 text-sm", status.className)}>
            {status.label}
          </Badge>
        </div>
      </div>

      {knowledgeMap.summary ? (
        <p className="font-goal text-foreground max-w-3xl text-xl leading-relaxed">
          {knowledgeMap.summary}
        </p>
      ) : null}

      {knowledgeMap.warnings.length > 0 ? (
        <div className="bg-warning-tint text-warning flex flex-col gap-1.5 rounded-xl px-4 py-3.5">
          <div className="flex items-center gap-1.5 text-xs font-semibold">
            <AlertTriangle className="size-3.5" />
            Warnings
          </div>
          <ul className="flex flex-col gap-1">
            {knowledgeMap.warnings.map((warning) => (
              <li key={warning} className="text-[13px] leading-relaxed">
                {warning}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="flex flex-wrap items-stretch gap-5">
        <ConceptGraph
          concepts={knowledgeMap.concepts}
          selectedConceptId={selectedConcept.concept_id}
          onSelectConcept={navigateToConcept}
        />
        <ConceptDetailPanel
          concept={selectedConcept}
          conceptsById={conceptsById}
          onSelectConcept={navigateToConcept}
        />
      </div>
    </div>
  );
}

function KnowledgeMapSkeleton() {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-start justify-between gap-6">
        <div className="flex flex-col gap-3">
          <Skeleton className="h-3 w-32" />
          <Skeleton className="h-9 w-72 max-w-full" />
        </div>
        <Skeleton className="h-7 w-24 rounded-full" />
      </div>
      <Skeleton className="h-16 w-full max-w-3xl rounded-lg" />
      <div className="flex flex-wrap gap-5">
        <Skeleton className="h-[480px] flex-[2_1_520px] rounded-2xl" />
        <Skeleton className="h-[480px] flex-1 rounded-2xl" />
      </div>
    </div>
  );
}

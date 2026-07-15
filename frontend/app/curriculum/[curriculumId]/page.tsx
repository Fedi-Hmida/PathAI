"use client";

import * as React from "react";
import { useParams, usePathname, useRouter, useSearchParams } from "next/navigation";

import { RequireAuth } from "@/components/auth/require-auth";
import { WeekPanel } from "@/components/curriculum/week-panel";
import { WeekTrail } from "@/components/curriculum/week-trail";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/client";
import { getCurriculum } from "@/lib/api/curriculum";
import { getKnowledgeMap } from "@/lib/api/knowledge-map";
import { getProgress } from "@/lib/api/progress";
import { getResource, getResourceAttachmentsByCurriculum } from "@/lib/api/resource";
import type { CurriculumDTO } from "@/lib/types/curriculum";
import type { KnowledgeMapDTO } from "@/lib/types/knowledge-map";
import type { ProgressStateDTO } from "@/lib/types/progress";
import type { ResourceAttachmentDTO, ResourceDTO } from "@/lib/types/resource";

type CurriculumLoadState =
  | { kind: "loading" }
  | { kind: "not_found" }
  | { kind: "invalid_id" }
  | { kind: "generation_unavailable" }
  | { kind: "ready"; curriculum: CurriculumDTO }
  | { kind: "error"; message: string };

export default function CurriculumWeekDetailPage() {
  return (
    <RequireAuth>
      <React.Suspense fallback={<CurriculumSkeleton />}>
        <CurriculumWeekDetailView />
      </React.Suspense>
    </RequireAuth>
  );
}

function CurriculumWeekDetailView() {
  const params = useParams<{ curriculumId: string }>();
  const curriculumId = params.curriculumId;
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();

  const progressId = searchParams.get("progressId");
  const knowledgeMapId = searchParams.get("knowledgeMapId");
  const weekParam = searchParams.get("week");

  const [loadedCurriculumId, setLoadedCurriculumId] = React.useState(curriculumId);
  const [state, setState] = React.useState<CurriculumLoadState>({ kind: "loading" });
  const [reloadNonce, setReloadNonce] = React.useState(0);
  const [attachments, setAttachments] = React.useState<ResourceAttachmentDTO[]>([]);
  const [resourceTitles, setResourceTitles] = React.useState<Map<string, ResourceDTO>>(new Map());
  const requestedResourceIdsRef = React.useRef<Set<string>>(new Set());

  const [loadedProgressId, setLoadedProgressId] = React.useState(progressId);
  const [progress, setProgress] = React.useState<ProgressStateDTO | null>(null);
  const [loadedKnowledgeMapId, setLoadedKnowledgeMapId] = React.useState(knowledgeMapId);
  const [knowledgeMap, setKnowledgeMap] = React.useState<KnowledgeMapDTO | null>(null);

  // Reset to loading during render when curriculumId changes, same pattern
  // as the Dashboard/Orchestration pages.
  if (curriculumId !== loadedCurriculumId) {
    setLoadedCurriculumId(curriculumId);
    setState({ kind: "loading" });
    setAttachments([]);
    setResourceTitles(new Map());
  }
  if (progressId !== loadedProgressId) {
    setLoadedProgressId(progressId);
    setProgress(null);
  }
  if (knowledgeMapId !== loadedKnowledgeMapId) {
    setLoadedKnowledgeMapId(knowledgeMapId);
    setKnowledgeMap(null);
  }

  const retry = React.useCallback(() => {
    setState({ kind: "loading" });
    setReloadNonce((nonce) => nonce + 1);
  }, []);

  React.useEffect(() => {
    let cancelled = false;
    requestedResourceIdsRef.current = new Set();

    getCurriculum(curriculumId)
      .then((curriculum) => {
        if (!cancelled) {
          setState({ kind: "ready", curriculum });
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
        // The curriculum couldn't be generated (LLM unavailable): show an
        // honest retry panel rather than falling through to placeholder content.
        if (error instanceof ApiError && error.code === "generation_unavailable") {
          setState({ kind: "generation_unavailable" });
          return;
        }
        // CurriculumId requires a "curriculum_" prefix + pattern
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

    getResourceAttachmentsByCurriculum(curriculumId)
      .then((result) => {
        if (!cancelled) {
          setAttachments(result);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setAttachments([]);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [curriculumId, reloadNonce]);

  // progress_id and knowledge_map_id are optional context passed in via
  // query params (there is no by-curriculum lookup for either). Absent or
  // failed fetches degrade to null rather than fabricating data.
  React.useEffect(() => {
    let cancelled = false;
    if (progressId === null) {
      return;
    }
    getProgress(progressId)
      .then((result) => {
        if (!cancelled) {
          setProgress(result);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setProgress(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [progressId]);

  React.useEffect(() => {
    let cancelled = false;
    if (knowledgeMapId === null) {
      return;
    }
    getKnowledgeMap(knowledgeMapId)
      .then((result) => {
        if (!cancelled) {
          setKnowledgeMap(result);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setKnowledgeMap(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [knowledgeMapId]);

  // Resource titles have no batch endpoint, so they're fetched lazily
  // per unique resource_id the first time a topic's resource list is
  // expanded, and cached here so re-expanding or revisiting a topic
  // across weeks doesn't refetch.
  const handleRequestResourceTitles = React.useCallback((resourceIds: string[]) => {
    const toFetch = resourceIds.filter((id) => !requestedResourceIdsRef.current.has(id));
    if (toFetch.length === 0) {
      return;
    }
    toFetch.forEach((id) => requestedResourceIdsRef.current.add(id));
    toFetch.forEach((resourceId) => {
      getResource(resourceId)
        .then((resource) => {
          setResourceTitles((prev) => {
            const next = new Map(prev);
            next.set(resourceId, resource);
            return next;
          });
        })
        .catch(() => {
          requestedResourceIdsRef.current.delete(resourceId);
        });
    });
  }, []);

  const navigateToWeek = React.useCallback(
    (weekNumber: number) => {
      const next = new URLSearchParams(searchParams.toString());
      next.set("week", String(weekNumber));
      router.replace(`${pathname}?${next.toString()}`, { scroll: false });
    },
    [pathname, router, searchParams]
  );

  if (state.kind === "loading") {
    return <CurriculumSkeleton />;
  }

  if (state.kind === "error") {
    return (
      <Alert variant="destructive">
        <AlertTitle>Couldn&apos;t load this curriculum</AlertTitle>
        <AlertDescription>{state.message}</AlertDescription>
      </Alert>
    );
  }

  if (state.kind === "invalid_id") {
    return (
      <p className="text-muted-foreground text-sm">
        That doesn&apos;t look like a valid curriculum ID.
      </p>
    );
  }

  if (state.kind === "generation_unavailable") {
    return (
      <Alert variant="destructive">
        <AlertTitle>We couldn&apos;t generate your curriculum yet</AlertTitle>
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
    return <p className="text-muted-foreground text-sm">Curriculum not found.</p>;
  }

  const { curriculum } = state;
  const weeks = curriculum.weeks;
  const requestedWeekNumber = weekParam ? Number(weekParam) : null;
  const selectedWeek =
    weeks.find((week) => week.week_number === requestedWeekNumber) ?? weeks[0]!;
  const selectedIndex = weeks.indexOf(selectedWeek);
  const prevWeek = selectedIndex > 0 ? weeks[selectedIndex - 1]! : null;
  const nextWeek = selectedIndex < weeks.length - 1 ? weeks[selectedIndex + 1]! : null;

  const conceptsById = knowledgeMap
    ? new Map(knowledgeMap.concepts.map((concept) => [concept.concept_id, concept]))
    : null;

  const attachmentsByTopicId = new Map<string, ResourceAttachmentDTO[]>();
  for (const attachment of attachments) {
    const list = attachmentsByTopicId.get(attachment.topic_id) ?? [];
    list.push(attachment);
    attachmentsByTopicId.set(attachment.topic_id, list);
  }
  for (const list of attachmentsByTopicId.values()) {
    list.sort((a, b) => a.rank - b.rank);
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
          Curriculum
        </span>
        <h2 className="font-goal text-foreground mt-1 text-lg font-medium">{curriculum.title}</h2>
      </div>

      <WeekTrail
        weeks={weeks}
        progress={progress}
        selectedWeekNumber={selectedWeek.week_number}
        onSelectWeek={navigateToWeek}
      />

      <WeekPanel
        week={selectedWeek}
        prevWeek={prevWeek}
        nextWeek={nextWeek}
        onNavigateWeek={navigateToWeek}
        progress={progress}
        conceptsById={conceptsById}
        attachmentsByTopicId={attachmentsByTopicId}
        resourceTitles={resourceTitles}
        onRequestResourceTitles={handleRequestResourceTitles}
      />
    </div>
  );
}

function CurriculumSkeleton() {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-3">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-7 w-72 max-w-full" />
      </div>
      <Skeleton className="h-[70px] rounded-2xl" />
      <div className="flex flex-col gap-4">
        <Skeleton className="h-9 w-96 max-w-full" />
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-16 rounded-2xl" />
        ))}
      </div>
    </div>
  );
}

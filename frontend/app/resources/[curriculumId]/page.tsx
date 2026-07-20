"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { RequireAuth } from "@/components/auth/require-auth";
import { computeResourceCoverage } from "@/components/resources/coverage-math";
import { CoverageHeader } from "@/components/resources/coverage-header";
import { ResourceFilters } from "@/components/resources/resource-filters";
import { ResourceShelf } from "@/components/resources/resource-shelf";
import type { ResourceShelfItem } from "@/components/resources/resource-shelf";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/client";
import { getCurriculum } from "@/lib/api/curriculum";
import { getResource, getResourceAttachmentsByCurriculum } from "@/lib/api/resource";
import type { CurriculumDTO, CurriculumTopicDTO, DifficultyLevel } from "@/lib/types/curriculum";
import type { ResourceAttachmentDTO, ResourceDTO, ResourceType } from "@/lib/types/resource";

type ResourcesLoadState =
  | { kind: "loading" }
  | { kind: "not_found" }
  | { kind: "invalid_id" }
  | {
      kind: "ready";
      curriculum: CurriculumDTO;
      attachments: ResourceAttachmentDTO[];
      resourcesById: Map<string, ResourceDTO>;
    }
  | { kind: "error"; message: string };

export default function ResourcesBrowserPage() {
  return (
    <RequireAuth>
      <React.Suspense fallback={<ResourcesBrowserSkeleton />}>
        <ResourcesBrowserView />
      </React.Suspense>
    </RequireAuth>
  );
}

function ResourcesBrowserView() {
  const params = useParams<{ curriculumId: string }>();
  const curriculumId = params.curriculumId;

  const [state, setState] = React.useState<ResourcesLoadState>({ kind: "loading" });
  const [activeTypes, setActiveTypes] = React.useState<ResourceType[]>([]);
  const [activeDifficulties, setActiveDifficulties] = React.useState<DifficultyLevel[]>([]);

  React.useEffect(() => {
    let cancelled = false;

    getCurriculum(curriculumId)
      .then(async (curriculum) => {
        const attachments = await getResourceAttachmentsByCurriculum(curriculumId);
        const uniqueResourceIds = Array.from(new Set(attachments.map((a) => a.resource_id)));
        const resources = await Promise.all(uniqueResourceIds.map((id) => getResource(id)));
        if (cancelled) {
          return;
        }
        const resourcesById = new Map(resources.map((resource) => [resource.resource_id, resource]));
        setState({ kind: "ready", curriculum, attachments, resourcesById });
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        if (error instanceof ApiError && error.status === 404) {
          setState({ kind: "not_found" });
          return;
        }
        // CurriculumId requires a "curr_" prefix + pattern (schemas/ids.py);
        // a malformed id fails FastAPI's request validation with 422 before
        // reaching the not-found path.
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
  }, [curriculumId]);

  const toggleType = (type: ResourceType) => {
    setActiveTypes((current) =>
      current.includes(type) ? current.filter((value) => value !== type) : [...current, type]
    );
  };

  const toggleDifficulty = (difficulty: DifficultyLevel) => {
    setActiveDifficulties((current) =>
      current.includes(difficulty)
        ? current.filter((value) => value !== difficulty)
        : [...current, difficulty]
    );
  };

  if (state.kind === "loading") {
    return <ResourcesBrowserSkeleton />;
  }

  if (state.kind === "error") {
    return (
      <Alert variant="destructive">
        <AlertTitle>Couldn&apos;t load this reading list</AlertTitle>
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

  if (state.kind === "not_found") {
    return <p className="text-muted-foreground text-sm">Curriculum not found.</p>;
  }

  const { curriculum, attachments, resourcesById } = state;
  const topics: CurriculumTopicDTO[] = curriculum.weeks.flatMap((week) => week.topics);
  const attachmentsByTopicId = new Map<string, ResourceAttachmentDTO[]>();
  for (const attachment of attachments) {
    const existing = attachmentsByTopicId.get(attachment.topic_id) ?? [];
    existing.push(attachment);
    attachmentsByTopicId.set(attachment.topic_id, existing);
  }

  const coverage = computeResourceCoverage(topics, attachments, resourcesById);

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center gap-3">
        <Link
          href={`/curriculum/${curriculumId}`}
          aria-label="Back to curriculum"
          className="border-border text-muted-foreground hover:bg-surface-sunken hover:text-foreground flex size-9 flex-none items-center justify-center rounded-full border"
        >
          <ArrowLeft className="size-4" />
        </Link>
        <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
          Resources · <span className="font-mono normal-case tracking-normal">{curriculum.curriculum_id}</span>
        </span>
      </div>

      <h1 className="font-goal text-foreground max-w-lg text-3xl leading-tight font-medium italic">
        Your reading list.
      </h1>

      <CoverageHeader
        topicsCovered={coverage.topicsCovered}
        topicsTotal={coverage.topicsTotal}
        averageRelevance={coverage.averageRelevance}
        distinctResourceTypeCount={coverage.distinctResourceTypeCount}
      />

      <ResourceFilters
        activeTypes={activeTypes}
        activeDifficulties={activeDifficulties}
        onToggleType={toggleType}
        onToggleDifficulty={toggleDifficulty}
      />

      <div className="flex flex-col gap-9">
        {topics.map((topic) => {
          const topicAttachments = attachmentsByTopicId.get(topic.topic_id) ?? [];
          const items: ResourceShelfItem[] = topicAttachments
            .slice()
            .sort((a, b) => a.rank - b.rank)
            .flatMap((attachment) => {
              const resource = resourcesById.get(attachment.resource_id);
              return resource ? [{ attachment, resource }] : [];
            });
          return (
            <ResourceShelf
              key={topic.topic_id}
              topic={topic}
              items={items}
              activeTypes={activeTypes}
              activeDifficulties={activeDifficulties}
            />
          );
        })}
      </div>

      <div className="border-border border-t pt-6">
        <Link
          href={`/curriculum/${curriculumId}`}
          className="text-brand text-sm font-semibold hover:underline"
        >
          View full curriculum <span aria-hidden="true">→</span>
        </Link>
      </div>
    </div>
  );
}

function ResourcesBrowserSkeleton() {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center gap-3">
        <Skeleton className="size-9 rounded-full" />
        <Skeleton className="h-3 w-32" />
      </div>
      <Skeleton className="h-9 w-72" />
      <Skeleton className="h-16 w-full" />
      <div className="flex flex-col gap-3">
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-8 w-2/3" />
      </div>
      <div className="flex flex-col gap-9">
        <Skeleton className="h-40 w-full rounded-xl" />
        <Skeleton className="h-40 w-full rounded-xl" />
      </div>
    </div>
  );
}

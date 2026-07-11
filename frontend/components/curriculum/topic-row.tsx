"use client";

import * as React from "react";
import { ChevronDown, Dumbbell, Eye, Flag, Paperclip, Sparkles, SquareCheck } from "lucide-react";

import { ConceptChip } from "@/components/curriculum/concept-chip";
import { cn } from "@/lib/utils";
import type { CurriculumTopicDTO, DifficultyLevel } from "@/lib/types/curriculum";
import type { ConceptMasteryDTO } from "@/lib/types/knowledge-map";
import type { TopicProgressDTO, TopicProgressStatus } from "@/lib/types/progress";
import type { ResourceAttachmentDTO, ResourceDTO } from "@/lib/types/resource";

const DIFFICULTY_CONFIG: Record<DifficultyLevel, { label: string; className: string }> = {
  beginner: { label: "Beginner", className: "bg-surface-sunken text-tertiary" },
  intermediate: { label: "Intermediate", className: "bg-brand-tint text-brand" },
  advanced: { label: "Advanced", className: "bg-warning-tint text-warning" },
};

function TopicMarker({ status }: { status: TopicProgressStatus | null }) {
  if (status === null) {
    return (
      <div className="border-border/70 size-[26px] flex-none rounded-full border-2 border-dashed" />
    );
  }
  if (status === "completed") {
    return (
      <div className="bg-success flex size-[26px] flex-none items-center justify-center rounded-full">
        <SquareCheck className="size-3.5 text-white" strokeWidth={2.5} />
      </div>
    );
  }
  if (status === "stuck") {
    return (
      <div className="bg-warning flex size-[26px] flex-none items-center justify-center rounded-full">
        <Flag className="size-3 text-white" fill="white" strokeWidth={0} />
      </div>
    );
  }
  if (status === "needs_review") {
    return (
      <div className="bg-danger flex size-[26px] flex-none items-center justify-center rounded-full">
        <Eye className="size-3.5 text-white" strokeWidth={2.5} />
      </div>
    );
  }
  if (status === "in_progress") {
    return (
      <div className="border-brand bg-brand-tint motion-safe:animate-pulse flex size-[26px] flex-none items-center justify-center rounded-full border-2">
        <div className="bg-brand size-2 rounded-full" />
      </div>
    );
  }
  return <div className="border-border size-[26px] flex-none rounded-full border-2" />;
}

type TopicRowProps = {
  topic: CurriculumTopicDTO;
  progress: TopicProgressDTO | null;
  conceptsById: Map<string, ConceptMasteryDTO> | null;
  attachments: ResourceAttachmentDTO[];
  resourceTitles: Map<string, ResourceDTO>;
  onRequestResourceTitles: (resourceIds: string[]) => void;
};

export function TopicRow({
  topic,
  progress,
  conceptsById,
  attachments,
  resourceTitles,
  onRequestResourceTitles,
}: TopicRowProps) {
  const [expanded, setExpanded] = React.useState(false);
  const [resourcesExpanded, setResourcesExpanded] = React.useState(false);
  const difficulty = DIFFICULTY_CONFIG[topic.difficulty];

  const handleToggleResources = () => {
    const next = !resourcesExpanded;
    setResourcesExpanded(next);
    if (next && attachments.length > 0) {
      onRequestResourceTitles(attachments.map((attachment) => attachment.resource_id));
    }
  };

  return (
    <div className="border-border bg-card overflow-hidden rounded-2xl border shadow-sm">
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        className="hover:bg-surface-sunken flex w-full items-center gap-3.5 px-5 py-4 text-left"
      >
        <TopicMarker status={progress?.status ?? null} />

        <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2">
          <span className="text-foreground text-[15px] font-medium">{topic.title}</span>
          {topic.adaptation_origin ? (
            <span className="bg-warning-tint text-warning inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold whitespace-nowrap">
              <Sparkles className="size-2.5" />
              {topic.adaptation_origin}
            </span>
          ) : null}
          <span
            className={cn(
              "rounded-full px-2.5 py-0.5 text-[11px] font-semibold whitespace-nowrap",
              difficulty.className
            )}
          >
            {difficulty.label}
          </span>
        </div>

        <span className="text-tertiary font-mono text-[13px] flex-none">{topic.estimated_hours}h</span>
        <ChevronDown
          className={cn(
            "text-tertiary size-[18px] flex-none transition-transform",
            expanded ? "rotate-180" : ""
          )}
        />
      </button>

      {expanded ? (
        <div className="flex flex-col gap-4.5 px-5 pt-0 pb-5.5 pl-[58px]">
          <p className="text-muted-foreground max-w-xl text-sm leading-relaxed">
            {topic.description}
          </p>

          {topic.concept_ids.length > 0 ? (
            <div className="flex flex-wrap gap-2.5">
              {topic.concept_ids.map((conceptId) => (
                <ConceptChip
                  key={conceptId}
                  conceptId={conceptId}
                  concept={conceptsById?.get(conceptId) ?? null}
                />
              ))}
            </div>
          ) : null}

          {topic.learning_outcomes.length > 0 ? (
            <div className="flex flex-col gap-1.5">
              {topic.learning_outcomes.map((outcome) => (
                <div key={outcome} className="text-muted-foreground flex items-start gap-2 text-[13px] leading-relaxed">
                  <SquareCheck className="text-tertiary mt-0.5 size-3.5 flex-none" />
                  <span>{outcome}</span>
                </div>
              ))}
            </div>
          ) : null}

          {topic.practice_task ? (
            <div className="bg-surface-sunken flex items-start gap-3 rounded-xl px-4 py-3.5">
              <Dumbbell className="text-brand mt-0.5 size-4 flex-none" />
              <div>
                <div className="text-brand mb-1 text-[11px] font-bold tracking-wide uppercase">
                  Practice
                </div>
                <div className="text-muted-foreground text-[13px] leading-relaxed">
                  {topic.practice_task}
                </div>
              </div>
            </div>
          ) : null}

          {topic.assessment_checkpoint ? (
            <div className="border-brand bg-brand-tint flex items-start gap-3 rounded-xl border-[1.5px] px-4 py-3.5">
              <Flag className="text-brand mt-0.5 size-4 flex-none" />
              <div>
                <div className="text-brand mb-1 text-[11px] font-bold tracking-wide uppercase">
                  Checkpoint
                </div>
                <div className="text-foreground text-[13px] leading-relaxed">
                  {topic.assessment_checkpoint}
                </div>
              </div>
            </div>
          ) : null}

          {attachments.length > 0 ? (
            <div>
              <button
                type="button"
                onClick={handleToggleResources}
                className="border-border bg-card hover:bg-surface-sunken text-muted-foreground inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold"
              >
                <Paperclip className="size-3" />
                {attachments.length} resource{attachments.length === 1 ? "" : "s"} attached
                <ChevronDown
                  className={cn("size-3 transition-transform", resourcesExpanded ? "rotate-180" : "")}
                />
              </button>
              {resourcesExpanded ? (
                <div className="bg-surface-sunken mt-2 flex max-w-lg flex-col gap-2 rounded-xl px-3.5 py-3">
                  {attachments.map((attachment) => {
                    const resource = resourceTitles.get(attachment.resource_id);
                    return (
                      <div
                        key={attachment.attachment_id}
                        className="text-muted-foreground flex items-center justify-between gap-3.5 text-[13px]"
                      >
                        <span className="truncate">{resource?.title ?? "Loading…"}</span>
                        <span className="text-tertiary font-tabular font-mono text-xs flex-none">
                          {Math.round(attachment.relevance_score * 100)}%
                        </span>
                      </div>
                    );
                  })}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

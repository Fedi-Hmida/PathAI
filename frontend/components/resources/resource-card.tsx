import * as React from "react";
import { AlertTriangle, ChevronDown } from "lucide-react";

import { RESOURCE_TYPE_ICON } from "@/components/resources/resource-type-config";
import { Card, CardContent } from "@/components/ui/card";
import { scoreBand } from "@/lib/score-band";
import { cn } from "@/lib/utils";
import type { DifficultyLevel } from "@/lib/types/curriculum";
import type { ResourceAttachmentDTO, ResourceDTO } from "@/lib/types/resource";

const DIFFICULTY_CONFIG: Record<DifficultyLevel, { label: string; className: string }> = {
  beginner: { label: "Beginner", className: "bg-surface-sunken text-tertiary" },
  intermediate: { label: "Intermediate", className: "bg-brand-tint text-brand" },
  advanced: { label: "Advanced", className: "bg-warning-tint text-warning" },
};

const RELEVANCE_BAR_COLOR: Record<ReturnType<typeof scoreBand>, string> = {
  success: "bg-success",
  brand: "bg-brand",
  warning: "bg-warning",
};

export interface ResourceCardProps {
  attachment: ResourceAttachmentDTO;
  resource: ResourceDTO;
}

export function ResourceCard({ attachment, resource }: ResourceCardProps) {
  const [expanded, setExpanded] = React.useState(false);
  const Icon = RESOURCE_TYPE_ICON[resource.resource_type];
  const difficulty = DIFFICULTY_CONFIG[resource.difficulty];
  const relevancePercent = Math.round(attachment.relevance_score * 100);

  return (
    <button
      type="button"
      onClick={() => setExpanded((value) => !value)}
      aria-expanded={expanded}
      className="w-[212px] flex-none text-left"
    >
      <Card className="gap-0 py-4">
        <CardContent className="flex flex-col px-4">
          <div className="bg-surface-sunken mb-3 flex size-7 items-center justify-center rounded-lg">
            <Icon className="text-brand size-3.5" />
          </div>

          <div className="text-foreground min-h-9.5 line-clamp-2 text-[14.5px] leading-snug font-medium">
            {resource.title}
          </div>

          <div className="border-border my-2.5 border-t" />

          <div className="text-tertiary mb-2 truncate text-xs">{resource.source_name}</div>

          <div className="mb-2.5 flex items-center justify-between gap-2">
            <span className="text-tertiary font-mono text-[11.5px]">
              {resource.estimated_minutes} min
            </span>
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-[10.5px] font-semibold whitespace-nowrap",
                difficulty.className
              )}
            >
              {difficulty.label}
            </span>
          </div>

          <div className="bg-surface-sunken h-1 w-full overflow-hidden rounded-full">
            <div
              className={cn("h-full rounded-full", RELEVANCE_BAR_COLOR[scoreBand(attachment.relevance_score)])}
              style={{ width: `${relevancePercent}%` }}
            />
          </div>

          <div
            className={cn(
              "grid transition-[grid-template-rows] duration-200",
              expanded ? "mt-3 grid-rows-[1fr]" : "grid-rows-[0fr]"
            )}
          >
            <div className="flex flex-col gap-1.5 overflow-hidden">
              <p className="text-muted-foreground text-[12.5px] leading-relaxed">
                {attachment.selection_reason}
              </p>
              {attachment.warnings.map((warning) => (
                <div key={warning} className="text-warning flex items-start gap-1.5 text-[11.5px]">
                  <AlertTriangle className="mt-0.5 size-3 flex-none" />
                  <span>{warning}</span>
                </div>
              ))}
            </div>
          </div>

          <ChevronDown
            className={cn(
              "text-tertiary mx-auto mt-2 size-3.5 transition-transform",
              expanded ? "rotate-180" : ""
            )}
          />
        </CardContent>
      </Card>
    </button>
  );
}

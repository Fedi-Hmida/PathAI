import {
  Code2,
  Dumbbell,
  FileText,
  GraduationCap,
  ListChecks,
  Newspaper,
  ScrollText,
  Video,
  type LucideIcon,
} from "lucide-react";

import type { ResourceType } from "@/lib/types/resource";

export const RESOURCE_TYPES: ResourceType[] = [
  "documentation",
  "tutorial",
  "paper",
  "article",
  "video",
  "code_example",
  "exercise",
  "checklist",
];

export const RESOURCE_TYPE_ICON: Record<ResourceType, LucideIcon> = {
  documentation: FileText,
  tutorial: GraduationCap,
  paper: ScrollText,
  article: Newspaper,
  video: Video,
  code_example: Code2,
  exercise: Dumbbell,
  checklist: ListChecks,
};

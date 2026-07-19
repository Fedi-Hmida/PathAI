import { History } from "lucide-react";

export interface RevisionBadgeProps {
  attempt: number;
}

export function RevisionBadge({ attempt }: RevisionBadgeProps) {
  return (
    <span className="bg-brand-tint text-brand inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold whitespace-nowrap">
      <History className="size-3.5" />
      Revision {attempt}
    </span>
  );
}

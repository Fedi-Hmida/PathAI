import Link from "next/link";
import { ArrowRight } from "lucide-react";

import type { NextRecommendedAction } from "@/lib/types/progress";

export interface NextActionCardProps {
  action: NextRecommendedAction;
  curriculumId: string;
}

export function NextActionCard({ action, curriculumId }: NextActionCardProps) {
  return (
    <Link
      href={`/curriculum/${curriculumId}`}
      className="border-warning bg-warning-tint hover:shadow-md flex items-center justify-between gap-4.5 rounded-2xl border px-6 py-5 transition-shadow"
    >
      <div>
        <div className="text-foreground mb-1.5 text-[17px] font-semibold">{action.label}</div>
        <div className="text-muted-foreground text-sm leading-relaxed">{action.reason}</div>
      </div>
      <ArrowRight className="text-warning size-5 flex-none" />
    </Link>
  );
}

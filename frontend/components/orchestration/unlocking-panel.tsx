import { Check } from "lucide-react";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { OrchestrationRunDTO } from "@/lib/types/orchestration";

const UNLOCKS = [
  { key: "knowledge_map", label: "Knowledge map", node: "load_knowledge_map" },
  { key: "curriculum", label: "Curriculum", node: "load_curriculum" },
  { key: "resources", label: "Resources", node: "load_resources" },
  { key: "critic_review", label: "Critic review", node: "load_critic_review" },
  { key: "evaluation", label: "Evaluation", node: "load_evaluation" },
] as const;

type UnlockingPanelProps = {
  run: OrchestrationRunDTO;
};

export function UnlockingPanel({ run }: UnlockingPanelProps) {
  return (
    <Card className="w-[280px] flex-none gap-4 py-5">
      <CardHeader>
        <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
          Unlocking
        </span>
      </CardHeader>
      <CardContent className="flex flex-col gap-2.5">
        {UNLOCKS.map((unlock) => {
          const unlocked = run.completed_nodes.includes(unlock.node);
          return (
            <div
              key={unlock.key}
              className={cn(
                "flex items-center gap-2.5 rounded-lg border px-2.5 py-2",
                unlocked ? "bg-success-tint border-success-tint" : "border-transparent"
              )}
            >
              <span
                className={cn(
                  "flex size-5 flex-none items-center justify-center rounded-full border-[1.5px]",
                  unlocked ? "bg-success border-success" : "border-border bg-transparent"
                )}
              >
                {unlocked ? <Check className="size-2.5 text-white" strokeWidth={3} /> : null}
              </span>
              <span
                className={cn(
                  "text-[13.5px]",
                  unlocked ? "text-foreground font-semibold" : "text-tertiary font-medium"
                )}
              >
                {unlock.label}
              </span>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

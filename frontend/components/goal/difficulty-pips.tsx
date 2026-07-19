import { cn } from "@/lib/utils";
import type { DifficultyLevel } from "@/lib/types/curriculum";

const LEVELS: DifficultyLevel[] = ["beginner", "intermediate", "advanced"];

export interface DifficultyPipsProps {
  level: DifficultyLevel;
}

export function DifficultyPips({ level }: DifficultyPipsProps) {
  const activeCount = LEVELS.indexOf(level) + 1;

  return (
    <div className="flex gap-1">
      {LEVELS.map((pipLevel, index) => (
        <span
          key={pipLevel}
          className={cn(
            "h-2 w-[22px] rounded-sm",
            index < activeCount ? "bg-brand" : "bg-surface-sunken"
          )}
        />
      ))}
    </div>
  );
}

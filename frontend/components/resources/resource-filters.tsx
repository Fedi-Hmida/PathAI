import { RESOURCE_TYPES, RESOURCE_TYPE_ICON } from "@/components/resources/resource-type-config";
import { cn, formatConceptLabel } from "@/lib/utils";
import type { DifficultyLevel } from "@/lib/types/curriculum";
import type { ResourceType } from "@/lib/types/resource";

const DIFFICULTIES: DifficultyLevel[] = ["beginner", "intermediate", "advanced"];

const DIFFICULTY_DOT_COLOR: Record<DifficultyLevel, string> = {
  beginner: "var(--success)",
  intermediate: "var(--brand)",
  advanced: "var(--warning)",
};

const CHIP_BASE =
  "inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[12.5px] font-medium";
const CHIP_INACTIVE = "border-border bg-card text-muted-foreground";
const CHIP_ACTIVE = "border-brand bg-brand-tint text-foreground";

export interface ResourceFiltersProps {
  activeTypes: ResourceType[];
  activeDifficulties: DifficultyLevel[];
  onToggleType: (type: ResourceType) => void;
  onToggleDifficulty: (difficulty: DifficultyLevel) => void;
}

export function ResourceFilters({
  activeTypes,
  activeDifficulties,
  onToggleType,
  onToggleDifficulty,
}: ResourceFiltersProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-tertiary mr-1 text-[11px] font-semibold tracking-wide uppercase">
          Format
        </span>
        {RESOURCE_TYPES.map((type) => {
          const Icon = RESOURCE_TYPE_ICON[type];
          const active = activeTypes.includes(type);
          return (
            <button
              key={type}
              type="button"
              onClick={() => onToggleType(type)}
              aria-pressed={active}
              className={cn(CHIP_BASE, active ? CHIP_ACTIVE : CHIP_INACTIVE)}
            >
              <Icon className={cn("size-3.5", active ? "text-brand" : "text-muted-foreground")} />
              {formatConceptLabel(type)}
            </button>
          );
        })}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <span className="text-tertiary mr-1 text-[11px] font-semibold tracking-wide uppercase">
          Difficulty
        </span>
        {DIFFICULTIES.map((difficulty) => {
          const active = activeDifficulties.includes(difficulty);
          return (
            <button
              key={difficulty}
              type="button"
              onClick={() => onToggleDifficulty(difficulty)}
              aria-pressed={active}
              className={cn(CHIP_BASE, active ? CHIP_ACTIVE : CHIP_INACTIVE)}
            >
              <span
                className="size-1.5 rounded-full"
                style={{ backgroundColor: DIFFICULTY_DOT_COLOR[difficulty] }}
              />
              {formatConceptLabel(difficulty)}
            </button>
          );
        })}
      </div>
    </div>
  );
}

import { cn } from "@/lib/utils";

export interface QuizOptionListProps {
  options: string[];
  selected: string | null;
  onSelect: (option: string) => void;
}

export function QuizOptionList({ options, selected, onSelect }: QuizOptionListProps) {
  return (
    <div className="flex flex-col gap-2.5" role="radiogroup">
      {options.map((option) => {
        const isSelected = option === selected;
        return (
          <button
            key={option}
            type="button"
            role="radio"
            aria-checked={isSelected}
            onClick={() => onSelect(option)}
            className={cn(
              "rounded-xl border px-4 py-3 text-left text-sm font-medium transition-colors",
              isSelected
                ? "border-brand bg-brand-tint text-brand"
                : "border-border text-foreground hover:bg-surface-sunken"
            )}
          >
            {option}
          </button>
        );
      })}
    </div>
  );
}

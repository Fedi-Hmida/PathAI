import { cn } from "@/lib/utils";

const RATING_VALUES = [1, 2, 3, 4, 5] as const;

type SelfRatingScaleProps = {
  value: number | null;
  onChange: (value: number) => void;
  disabled: boolean;
};

export function SelfRatingScale({ value, onChange, disabled }: SelfRatingScaleProps) {
  return (
    <div className="flex gap-1.5">
      {RATING_VALUES.map((rating) => {
        const active = value === rating;
        return (
          <button
            key={rating}
            type="button"
            disabled={disabled}
            onClick={() => onChange(rating)}
            aria-pressed={active}
            className={cn(
              "flex size-9 items-center justify-center rounded-md border text-[13px] font-semibold transition-colors",
              active
                ? "border-brand bg-brand-tint text-brand"
                : "border-border text-muted-foreground hover:border-brand-border",
              disabled && "cursor-default opacity-70"
            )}
          >
            {rating}
          </button>
        );
      })}
    </div>
  );
}

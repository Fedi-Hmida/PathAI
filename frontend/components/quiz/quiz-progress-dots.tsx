import { cn } from "@/lib/utils";

export interface QuizProgressDotsProps {
  total: number;
  currentIndex: number;
  answeredIndexes: ReadonlySet<number>;
}

export function QuizProgressDots({ total, currentIndex, answeredIndexes }: QuizProgressDotsProps) {
  return (
    <div className="flex items-center justify-center gap-2" role="img" aria-label={`Question ${currentIndex + 1} of ${total}`}>
      {Array.from({ length: total }).map((_, index) => (
        <span
          key={index}
          className={cn(
            "size-2.5 rounded-full transition-colors",
            index === currentIndex
              ? "bg-brand"
              : answeredIndexes.has(index)
                ? "bg-success"
                : "bg-surface-sunken"
          )}
        />
      ))}
    </div>
  );
}

type LiveAssessmentHeaderProps = {
  goalText: string;
  questionNumber: number;
  totalQuestions: number;
  confidence: number;
};

export function LiveAssessmentHeader({
  goalText,
  questionNumber,
  totalQuestions,
  confidence,
}: LiveAssessmentHeaderProps) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <div className="mb-2.5 flex items-center gap-2">
          <span className="bg-brand size-[7px] flex-none animate-pulse rounded-full" />
          <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
            Diagnostic in progress
          </span>
        </div>
        <h1 className="font-goal text-foreground max-w-2xl text-[26px] leading-snug font-medium italic">
          {goalText}
        </h1>
      </div>

      <div className="border-border bg-card flex flex-wrap items-center gap-6 rounded-2xl border px-6 py-5 shadow-sm">
        <div>
          <div className="text-tertiary mb-1 text-[11px] font-semibold tracking-wide uppercase">
            Progress
          </div>
          <div className="text-foreground font-tabular text-[15px] font-semibold">
            Question {questionNumber}{" "}
            <span className="text-tertiary text-sm font-medium">of {totalQuestions}</span>
          </div>
        </div>
        <div className="bg-border h-8 w-px flex-none" />
        <div className="min-w-[160px] flex-1">
          <div className="text-tertiary mb-1 text-[11px] font-semibold tracking-wide uppercase">
            Confidence
          </div>
          <div className="bg-surface-sunken relative h-2 overflow-hidden rounded-full">
            <div
              className="bg-brand absolute inset-y-0 left-0 rounded-full transition-all"
              style={{ width: `${Math.round(Math.max(0, Math.min(1, confidence)) * 100)}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

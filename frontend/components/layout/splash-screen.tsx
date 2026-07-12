export function SplashScreen() {
  return (
    <div
      role="status"
      aria-live="polite"
      className="bg-background fixed inset-0 z-50 flex min-h-screen flex-col items-center justify-center gap-6"
    >
      <span className="sr-only">Loading PathAI…</span>

      <div className="bg-brand-tint animate-pathai-pulse flex size-16 items-center justify-center rounded-2xl">
        <span className="font-goal text-brand text-2xl font-semibold">P</span>
      </div>

      <span className="font-goal animate-pathai-fade-in text-foreground text-xl font-medium tracking-tight">
        PathAI
      </span>

      <div className="bg-border relative h-1 w-40 overflow-hidden rounded-full">
        <div className="bg-brand animate-pathai-shimmer absolute inset-y-0 w-1/3 rounded-full" />
      </div>
    </div>
  );
}

import { AlertTriangle } from "lucide-react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import type { AdaptationSummary } from "@/lib/types/dashboard";

type AdaptationBannerProps = {
  adaptationSummary: AdaptationSummary | null;
};

export function AdaptationBanner({ adaptationSummary }: AdaptationBannerProps) {
  const events = adaptationSummary?.recent_events ?? [];
  const message =
    events.length > 0
      ? events[events.length - 1]
      : "Your learning plan was recently adjusted.";

  return (
    <Alert className="border-warning bg-warning-tint">
      <AlertTriangle className="text-warning" />
      <AlertDescription className="text-foreground font-medium">{message}</AlertDescription>
    </Alert>
  );
}

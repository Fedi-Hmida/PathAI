"use client";

import * as React from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/client";
import { getHealth } from "@/lib/api/health";
import type { HealthStatus } from "@/lib/types/health";

type LoadState =
  | { kind: "loading" }
  | { kind: "ready"; health: HealthStatus }
  | { kind: "error"; message: string };

export default function Home() {
  const [state, setState] = React.useState<LoadState>({ kind: "loading" });

  React.useEffect(() => {
    let cancelled = false;

    getHealth()
      .then((health) => {
        if (!cancelled) {
          setState({ kind: "ready", health });
        }
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        const message =
          error instanceof ApiError
            ? error.message
            : "Unable to reach the PathAI backend.";
        setState({ kind: "error", message });
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">PathAI</h1>
        <p className="text-muted-foreground">
          Personalized learning-path generator.
        </p>
      </div>

      <Card className="max-w-md">
        <CardHeader>
          <CardTitle>Backend status</CardTitle>
          <CardDescription>
            Live check against the API health endpoint.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {state.kind === "loading" && (
            <div className="flex items-center gap-2">
              <Skeleton className="h-5 w-16 rounded-full" />
              <Skeleton className="h-5 w-40" />
            </div>
          )}

          {state.kind === "ready" && (
            <div className="flex items-center gap-2 text-sm">
              <Badge variant={state.health.status === "ok" ? "default" : "secondary"}>
                {state.health.status}
              </Badge>
              <span className="text-muted-foreground">
                {state.health.service} &middot; {state.health.environment}
              </span>
            </div>
          )}

          {state.kind === "error" && (
            <Alert variant="destructive">
              <AlertTitle>Backend unavailable</AlertTitle>
              <AlertDescription>{state.message}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

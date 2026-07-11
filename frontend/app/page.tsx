"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";
import { Skeleton } from "@/components/ui/skeleton";
import { getMyWorkspace } from "@/lib/api/workspace";
import { DEMO_RUN_ID } from "@/lib/types/orchestration";

export default function Home() {
  const { status, authEnabled } = useAuth();
  const router = useRouter();

  React.useEffect(() => {
    if (authEnabled === null || status === "loading") {
      return;
    }

    if (!authEnabled) {
      // No-auth mode (the default): behave exactly as before this feature -
      // a single shared demo run for everyone.
      router.replace(`/dashboard/${DEMO_RUN_ID}`);
      return;
    }

    if (status === "anonymous") {
      router.replace("/login");
      return;
    }

    // Authenticated with auth on: route to the caller's own workspace, or
    // the empty-state screen if they haven't created one yet.
    let cancelled = false;
    getMyWorkspace()
      .then((workspace) => {
        if (cancelled) {
          return;
        }
        router.replace(workspace ? `/dashboard/${workspace.run_id}` : "/workspace");
      })
      .catch(() => {
        if (!cancelled) {
          router.replace("/workspace");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [authEnabled, status, router]);

  return (
    <div className="flex flex-col gap-3">
      <Skeleton className="h-7 w-56" />
      <Skeleton className="h-32 rounded-2xl" />
    </div>
  );
}

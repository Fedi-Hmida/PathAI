"use client";

import { useEffect, useState } from "react";

import { StatusBadge, type StatusTone } from "@/components/ui";
import { PathAIFrontendApiError } from "@/lib/api/client";
import { getHealth, getReadiness, getSafeLlmConfig } from "@/lib/api/runtime";
import type { HealthResponse, ReadinessResponse, SafeLLMConfig } from "@/lib/api/types";

import styles from "./TopStatusBar.module.css";

type RuntimeState = {
  health?: HealthResponse;
  llm?: SafeLLMConfig;
  llmError?: string;
  loading: boolean;
  readiness?: ReadinessResponse;
  runtimeError?: string;
};

export function TopStatusBar() {
  const [state, setState] = useState<RuntimeState>({ loading: true });

  useEffect(() => {
    let cancelled = false;

    async function loadRuntimeStatus() {
      const [healthResult, readinessResult, llmResult] = await Promise.allSettled([
        getHealth(),
        getReadiness(),
        getSafeLlmConfig()
      ]);

      if (cancelled) {
        return;
      }

      const nextState: RuntimeState = { loading: false };

      if (healthResult.status === "fulfilled") {
        nextState.health = healthResult.value;
      } else {
        nextState.runtimeError = toSafeErrorMessage(healthResult.reason);
      }

      if (readinessResult.status === "fulfilled") {
        nextState.readiness = readinessResult.value;
      } else if (!nextState.runtimeError) {
        nextState.runtimeError = toSafeErrorMessage(readinessResult.reason);
      }

      if (llmResult.status === "fulfilled") {
        nextState.llm = llmResult.value;
      } else {
        nextState.llmError = toSafeErrorMessage(llmResult.reason);
      }

      setState(nextState);
    }

    void loadRuntimeStatus();

    return () => {
      cancelled = true;
    };
  }, []);

  const backendTone: StatusTone = state.health ? "success" : state.loading ? "neutral" : "danger";
  const readyTone: StatusTone =
    state.readiness?.status === "ready" ? "success" : state.loading ? "neutral" : "warning";
  const llmTone: StatusTone = state.llm ? (state.llm.mock_mode ? "warning" : "success") : "neutral";

  return (
    <div aria-label="Runtime status" className={styles.statusBar}>
      <StatusItem
        label="Backend"
        tone={backendTone}
        value={state.loading ? "Checking" : state.health ? "Online" : "Offline"}
      />
      <StatusItem
        label="Readiness"
        tone={readyTone}
        value={
          state.loading
            ? "Checking"
            : state.readiness?.status === "ready"
              ? "Ready"
              : "Not ready"
        }
      />
      <StatusItem
        label="LLM"
        tone={llmTone}
        value={
          state.loading
            ? "Checking"
            : state.llm
              ? state.llm.mock_mode
                ? "Mock mode"
                : "Real mode"
              : "Unavailable"
        }
      />
      <StatusItem label="Mode" tone="info" value="No auth local" />
      {(state.runtimeError || state.llmError) && (
        <span className={styles.muted} title={state.runtimeError ?? state.llmError}>
          Status details available on hover
        </span>
      )}
    </div>
  );
}

function StatusItem({ label, tone, value }: { label: string; tone: StatusTone; value: string }) {
  return (
    <div className={styles.statusItem}>
      <span className={styles.label}>{label}</span>
      <span className={styles.value}>
        <StatusBadge tone={tone}>{value}</StatusBadge>
      </span>
    </div>
  );
}

function toSafeErrorMessage(error: unknown): string {
  if (error instanceof PathAIFrontendApiError) {
    return `${error.status}: ${error.message}`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Runtime status unavailable.";
}

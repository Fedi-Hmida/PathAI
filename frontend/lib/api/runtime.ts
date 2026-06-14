import { requestJson } from "./client";
import type { HealthResponse, ReadinessResponse, SafeLLMConfig } from "./types";

export function getHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/health");
}

export function getReadiness(): Promise<ReadinessResponse> {
  return requestJson<ReadinessResponse>("/ready");
}

export function getSafeLlmConfig(): Promise<SafeLLMConfig> {
  return requestJson<SafeLLMConfig>("/dev/llm/config");
}

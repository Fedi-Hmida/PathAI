export type ApiErrorEnvelope = {
  detail?: string | { code?: string; details?: unknown; message?: string };
  error?: { code?: string; details?: unknown; message?: string };
};

export type ApiRequestOptions = RequestInit & {
  noStore?: boolean;
};

export type HealthResponse = {
  environment: string;
  service: string;
  status: string;
  version: string;
};

export type ReadinessResponse = {
  checks: Record<string, string>;
  environment: string;
  message?: string | null;
  service: string;
  status: "ready" | "not_ready";
  version: string;
};

export type SafeLLMConfig = {
  api_key_configured: boolean;
  api_url_configured: boolean;
  max_retries: number;
  mock_mode: boolean;
  model: string;
  prompt_version: string;
  retry_backoff_seconds: number;
  timeout_seconds: number;
};

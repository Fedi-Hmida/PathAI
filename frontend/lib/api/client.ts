import type { ApiErrorEnvelope, ApiRequestOptions } from "./types";

const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";

export class PathAIFrontendApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string,
    public readonly details?: unknown
  ) {
    super(message);
    this.name = "PathAIFrontendApiError";
  }
}

export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_API_BASE_URL;
}

export async function requestJson<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { noStore = true, ...init } = options;
  const headers = new Headers(init.headers);

  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    cache: noStore ? "no-store" : init.cache,
    headers
  });

  if (!response.ok) {
    throw await toApiError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

async function toApiError(response: Response): Promise<PathAIFrontendApiError> {
  try {
    const payload = (await response.json()) as ApiErrorEnvelope;
    const parsed = parseErrorEnvelope(payload);
    return new PathAIFrontendApiError(
      parsed.message ?? "PathAI API request failed",
      response.status,
      parsed.code,
      parsed.details
    );
  } catch {
    return new PathAIFrontendApiError("PathAI API request failed", response.status);
  }
}

function parseErrorEnvelope(payload: ApiErrorEnvelope): {
  code?: string;
  details?: unknown;
  message?: string;
} {
  if (payload.error) {
    return payload.error;
  }

  if (typeof payload.detail === "string") {
    return { message: payload.detail };
  }

  return payload.detail ?? {};
}

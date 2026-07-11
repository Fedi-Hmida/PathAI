import { getAccessToken, setAccessToken } from "@/lib/api/auth-token";

const DEFAULT_BASE_URL = "http://localhost:8000/api/v1";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_BASE_URL;

// Auth endpoints that must never trigger the 401 -> silent-refresh -> retry
// flow: a failed login/register is a real credentials error (not an expired
// session), and /auth/refresh failing IS the "session is gone" signal itself
// - retrying it would recurse.
const NO_REFRESH_RETRY_PATHS = new Set(["/auth/login", "/auth/register", "/auth/refresh"]);

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function extractErrorMessage(body: unknown): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") {
      return detail;
    }
  }
  return "Something went wrong. Please try again.";
}

async function parseJsonBody(response: Response): Promise<unknown> {
  if (response.status === 204) {
    return null;
  }
  try {
    return await response.json();
  } catch {
    return null;
  }
}

async function rawFetch(
  method: "GET" | "POST",
  path: string,
  body: unknown,
): Promise<Response> {
  const headers: Record<string, string> = { Accept: "application/json" };
  const token = getAccessToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const init: RequestInit = {
    method,
    headers,
    // Sends/receives the httpOnly refresh cookie. Safe cross-origin only
    // because the backend's CORS allow-list is explicit, never "*".
    credentials: "include",
  };
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  }
  try {
    return await fetch(`${API_BASE_URL}${path}`, init);
  } catch {
    throw new ApiError(0, "Unable to reach the PathAI backend.");
  }
}

// Mints a fresh access token from the httpOnly refresh cookie. Deduped via a
// single shared in-flight promise: on a fresh page load, AuthProvider's own
// bootstrap AND any data-fetching page mounted alongside it (which fires
// before the bootstrap's access token exists, so its request 401s and hits
// the interceptor below) would otherwise both race to call this endpoint.
// Since refresh tokens rotate on every use, two concurrent calls would each
// present the same soon-to-be-stale cookie - the second one to land trips
// reuse detection and revokes the whole session. Sharing one in-flight
// promise means every concurrent caller gets the one real result instead.
let inFlightRefresh: Promise<unknown> | null = null;

function refreshAccessToken<T>(): Promise<T> {
  if (!inFlightRefresh) {
    inFlightRefresh = doRefresh().finally(() => {
      inFlightRefresh = null;
    });
  }
  return inFlightRefresh as Promise<T>;
}

async function doRefresh(): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { Accept: "application/json" },
      credentials: "include",
    });
  } catch {
    throw new ApiError(0, "Unable to reach the PathAI backend.");
  }
  const parsed = await parseJsonBody(response);
  if (!response.ok) {
    setAccessToken(null);
    throw new ApiError(response.status, extractErrorMessage(parsed));
  }
  const body = parsed as { access_token?: string } | null;
  if (!body?.access_token) {
    setAccessToken(null);
    throw new ApiError(response.status, "Session refresh returned no access token.");
  }
  setAccessToken(body.access_token);
  return body;
}

async function request<T>(
  method: "GET" | "POST",
  path: string,
  body: unknown,
): Promise<T> {
  let response = await rawFetch(method, path, body);

  if (response.status === 401 && !NO_REFRESH_RETRY_PATHS.has(path)) {
    try {
      await refreshAccessToken();
      response = await rawFetch(method, path, body);
    } catch {
      // Refresh failed; fall through and surface the original 401 below.
    }
  }

  const parsed = await parseJsonBody(response);
  if (!response.ok) {
    throw new ApiError(response.status, extractErrorMessage(parsed));
  }
  return parsed as T;
}

// Exposed so AuthProvider's session bootstrap shares the exact same
// in-flight refresh call (and its dedup lock) as the request interceptor
// above, rather than issuing an independent, racing /auth/refresh call.
export function refreshSession<T>(): Promise<T> {
  return refreshAccessToken<T>();
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>("GET", path, undefined);
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>("POST", path, body);
}

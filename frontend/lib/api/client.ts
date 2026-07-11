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

// Attempts to mint a fresh access token from the httpOnly refresh cookie.
// Returns true and updates the in-memory token on success; on any failure
// clears the token (the client must be treated as logged out) and returns
// false. Never throws - callers decide what a failed refresh means.
async function attemptSilentRefresh(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { Accept: "application/json" },
      credentials: "include",
    });
    if (!response.ok) {
      setAccessToken(null);
      return false;
    }
    const body = (await parseJsonBody(response)) as { access_token?: string } | null;
    if (!body?.access_token) {
      setAccessToken(null);
      return false;
    }
    setAccessToken(body.access_token);
    return true;
  } catch {
    setAccessToken(null);
    return false;
  }
}

async function request<T>(
  method: "GET" | "POST",
  path: string,
  body: unknown,
): Promise<T> {
  let response = await rawFetch(method, path, body);

  if (response.status === 401 && !NO_REFRESH_RETRY_PATHS.has(path)) {
    const refreshed = await attemptSilentRefresh();
    if (refreshed) {
      response = await rawFetch(method, path, body);
    }
  }

  const parsed = await parseJsonBody(response);
  if (!response.ok) {
    throw new ApiError(response.status, extractErrorMessage(parsed));
  }
  return parsed as T;
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>("GET", path, undefined);
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>("POST", path, body);
}

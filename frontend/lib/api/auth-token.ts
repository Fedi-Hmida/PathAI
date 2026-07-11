// In-memory access token store. Deliberately not localStorage/sessionStorage
// (RULES.md: no secrets in browser storage) — the token lives only in JS
// memory and is re-established on page load via a silent refresh against the
// httpOnly refresh cookie (see components/auth/auth-provider.tsx).
let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

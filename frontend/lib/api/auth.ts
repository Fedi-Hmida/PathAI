import { apiGet, apiPost, refreshSession as sharedRefreshSession } from "@/lib/api/client";
import type {
  AuthSessionResponse,
  LoginRequest,
  RegisterRequest,
  UserDTO,
} from "@/lib/types/auth";

export function registerUser(payload: RegisterRequest): Promise<AuthSessionResponse> {
  return apiPost<AuthSessionResponse>("/auth/register", payload);
}

export function loginUser(payload: LoginRequest): Promise<AuthSessionResponse> {
  return apiPost<AuthSessionResponse>("/auth/login", payload);
}

// Delegates to the client's shared, deduped refresh call rather than issuing
// its own /auth/refresh request - see client.ts for why that dedup matters.
export function refreshSession(): Promise<AuthSessionResponse> {
  return sharedRefreshSession<AuthSessionResponse>();
}

export function logoutUser(): Promise<void> {
  return apiPost<void>("/auth/logout");
}

export function getCurrentUser(): Promise<UserDTO> {
  return apiGet<UserDTO>("/auth/me");
}

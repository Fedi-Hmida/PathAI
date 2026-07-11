import { apiGet, apiPost } from "@/lib/api/client";
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

export function refreshSession(): Promise<AuthSessionResponse> {
  return apiPost<AuthSessionResponse>("/auth/refresh");
}

export function logoutUser(): Promise<void> {
  return apiPost<void>("/auth/logout");
}

export function getCurrentUser(): Promise<UserDTO> {
  return apiGet<UserDTO>("/auth/me");
}

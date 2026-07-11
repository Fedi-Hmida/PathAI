"use client";

import * as React from "react";

import { getAuthConfig, loginUser, logoutUser, refreshSession, registerUser } from "@/lib/api/auth";
import { setAccessToken } from "@/lib/api/auth-token";
import type { LoginRequest, RegisterRequest, UserDTO } from "@/lib/types/auth";

type AuthStatus = "loading" | "authenticated" | "anonymous";

type AuthContextValue = {
  status: AuthStatus;
  user: UserDTO | null;
  // null while the /auth/config check is still in flight.
  authEnabled: boolean | null;
  login: (payload: LoginRequest) => Promise<void>;
  register: (payload: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = React.createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = React.useState<AuthStatus>("loading");
  const [user, setUser] = React.useState<UserDTO | null>(null);
  const [authEnabled, setAuthEnabled] = React.useState<boolean | null>(null);

  React.useEffect(() => {
    let cancelled = false;

    // Auth-off (the default no-auth demo) must be distinguishable from
    // "session not yet established" - otherwise the anonymous state after a
    // failed silent refresh looks identical in both cases. Ask the server
    // first, then only attempt the silent refresh if auth is actually on.
    getAuthConfig()
      .then((config) => {
        if (cancelled) {
          return;
        }
        setAuthEnabled(config.enabled);
        if (!config.enabled) {
          setStatus("anonymous");
          return;
        }
        // The in-memory access token doesn't survive a page reload; the
        // httpOnly refresh cookie does. Bootstrapping the session means
        // silently exchanging that cookie for a fresh access token on first
        // mount.
        refreshSession()
          .then((session) => {
            if (cancelled) {
              return;
            }
            setAccessToken(session.access_token);
            setUser(session.user);
            setStatus("authenticated");
          })
          .catch(() => {
            if (cancelled) {
              return;
            }
            setAccessToken(null);
            setUser(null);
            setStatus("anonymous");
          });
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        // Backend unreachable: treat as auth-off so the shared demo path
        // still renders instead of getting stuck on a loading state.
        setAuthEnabled(false);
        setStatus("anonymous");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const login = React.useCallback(async (payload: LoginRequest) => {
    const session = await loginUser(payload);
    setAccessToken(session.access_token);
    setUser(session.user);
    setStatus("authenticated");
  }, []);

  const register = React.useCallback(async (payload: RegisterRequest) => {
    const session = await registerUser(payload);
    setAccessToken(session.access_token);
    setUser(session.user);
    setStatus("authenticated");
  }, []);

  const logout = React.useCallback(async () => {
    try {
      await logoutUser();
    } finally {
      setAccessToken(null);
      setUser(null);
      setStatus("anonymous");
    }
  }, []);

  const value = React.useMemo<AuthContextValue>(
    () => ({ status, user, authEnabled, login, register, logout }),
    [status, user, authEnabled, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

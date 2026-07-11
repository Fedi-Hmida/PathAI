"use client";

import * as React from "react";

import { loginUser, logoutUser, refreshSession, registerUser } from "@/lib/api/auth";
import { setAccessToken } from "@/lib/api/auth-token";
import type { LoginRequest, RegisterRequest, UserDTO } from "@/lib/types/auth";

type AuthStatus = "loading" | "authenticated" | "anonymous";

type AuthContextValue = {
  status: AuthStatus;
  user: UserDTO | null;
  login: (payload: LoginRequest) => Promise<void>;
  register: (payload: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = React.createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = React.useState<AuthStatus>("loading");
  const [user, setUser] = React.useState<UserDTO | null>(null);

  React.useEffect(() => {
    let cancelled = false;

    // The in-memory access token doesn't survive a page reload; the httpOnly
    // refresh cookie does. Bootstrapping the session means silently
    // exchanging that cookie for a fresh access token on first mount. If
    // auth is disabled server-side (PATHAI_ENABLE_AUTH=false) this 404s and
    // the app simply stays anonymous - the no-auth demo is unaffected.
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
    () => ({ status, user, login, register, logout }),
    [status, user, login, register, logout],
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

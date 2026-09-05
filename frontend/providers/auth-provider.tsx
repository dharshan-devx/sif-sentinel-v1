"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { authApi, ApiError, setUnauthorizedHandler } from "@/lib/api";
import { tokenStore } from "@/lib/auth";
import type { AuthUser, LoginRequest } from "@/types/api";

export type AuthStatus = "loading" | "authenticated" | "unauthenticated" | "unavailable";

interface AuthContextValue {
  status: AuthStatus;
  user: AuthUser | null;
  signIn: (credentials: LoginRequest) => Promise<void>;
  refreshSession: () => Promise<void>;
  endSession: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<AuthUser | null>(null);
  const isEndingSession = useRef(false);

  const clearSession = useCallback(() => {
    tokenStore.clear();
    queryClient.clear();
    setUser(null);
    setStatus("unauthenticated");
  }, [queryClient]);

  const endSession = useCallback(() => {
    if (isEndingSession.current) return;
    isEndingSession.current = true;
    clearSession();
    router.replace("/login");
    queueMicrotask(() => { isEndingSession.current = false; });
  }, [clearSession, router]);

  const refreshSession = useCallback(async () => {
    if (!tokenStore.has()) {
      setUser(null);
      setStatus("unauthenticated");
      return;
    }
    setStatus("loading");
    try {
      const currentUser = await authApi.me();
      setUser(currentUser);
      setStatus("authenticated");
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        clearSession();
        return;
      }
      // A temporary reachability/service failure never invalidates a retained token.
      setStatus("unavailable");
    }
  }, [clearSession]);

  const signIn = useCallback(async (credentials: LoginRequest) => {
    const session = await authApi.login(credentials);
    tokenStore.set(session.access_token);
    setUser(session.user);
    setStatus("authenticated");
  }, []);

  // eslint-disable-next-line react-hooks/set-state-in-effect -- refreshSession is async; state updates happen in callbacks after the effect body completes, not synchronously within it.
  useEffect(() => { void refreshSession(); }, [refreshSession]);
  useEffect(() => {
    setUnauthorizedHandler(endSession);
    return () => setUnauthorizedHandler(undefined);
  }, [endSession]);

  const value = useMemo<AuthContextValue>(() => ({ status, user, signIn, refreshSession, endSession }), [endSession, refreshSession, signIn, status, user]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider.");
  return context;
}

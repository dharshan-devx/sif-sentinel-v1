"use client";

import { useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { authApi } from "@/lib/api/auth";
import { isApiClientError } from "@/lib/api/client";
import { tokenStore } from "@/lib/auth/token-store";
import type { LoginRequest, RegisterRequest, User } from "@/types/api";

interface AuthContextValue {
  user: User | null; status: "loading" | "authenticated" | "unauthenticated" | "unavailable"; initializationError: string | null;
  signIn: (payload: LoginRequest) => Promise<User>;
  register: (payload: RegisterRequest) => Promise<User>;
  signOut: () => void;
  refresh: () => Promise<User | null>;
}
const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthContextValue["status"]>("loading");
  const [initializationError, setInitializationError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const signOut = useCallback(() => { tokenStore.clear(); queryClient.clear(); setUser(null); setInitializationError(null); setStatus("unauthenticated"); }, [queryClient]);
  const refresh = useCallback(async (): Promise<User | null> => {
    if (!tokenStore.has()) { setUser(null); setInitializationError(null); setStatus("unauthenticated"); return null; }
    setStatus("loading");
    try { const current = await authApi.me(); setUser(current); setInitializationError(null); setStatus("authenticated"); return current; }
    catch (error) {
      if (isApiClientError(error) && error.status === 401) { signOut(); return null; }
      setInitializationError(isApiClientError(error) ? error.message : "We could not restore your session.");
      setStatus("unavailable");
      return null;
    }
  }, [signOut]);
  useEffect(() => { void refresh().catch(() => undefined); }, [refresh]);
  useEffect(() => { const onUnauthorized = () => signOut(); window.addEventListener("sif:unauthorized", onUnauthorized); return () => window.removeEventListener("sif:unauthorized", onUnauthorized); }, [signOut]);
  const signIn = useCallback(async (payload: LoginRequest) => {
    const response = await authApi.login(payload); tokenStore.set(response.access_token); setUser(response.user); setInitializationError(null); setStatus("authenticated"); return response.user;
  }, []);
  const register = useCallback((payload: RegisterRequest) => authApi.register(payload), []);
  const value = useMemo(() => ({ user, status, initializationError, signIn, register, signOut, refresh }), [user, status, initializationError, signIn, register, signOut, refresh]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}

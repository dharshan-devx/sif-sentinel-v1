"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { authApi } from "@/lib/api/auth";
import { isApiClientError } from "@/lib/api/client";
import { tokenStore } from "@/lib/auth/token-store";
import type { LoginRequest, RegisterRequest, User } from "@/types/api";

interface AuthContextValue {
  user: User | null; isLoading: boolean;
  signIn: (payload: LoginRequest) => Promise<User>;
  register: (payload: RegisterRequest) => Promise<User>;
  signOut: () => void;
  refresh: () => Promise<User | null>;
}
const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setLoading] = useState(true);
  const signOut = useCallback(() => { tokenStore.clear(); setUser(null); }, []);
  const refresh = useCallback(async (): Promise<User | null> => {
    if (!tokenStore.get()) { setLoading(false); return null; }
    try { const current = await authApi.me(); setUser(current); return current; }
    catch (error) { if (isApiClientError(error) && error.status === 401) signOut(); throw error; }
    finally { setLoading(false); }
  }, [signOut]);
  useEffect(() => { void refresh().catch(() => undefined); }, [refresh]);
  const signIn = useCallback(async (payload: LoginRequest) => {
    const response = await authApi.login(payload); tokenStore.set(response.access_token); setUser(response.user); return response.user;
  }, []);
  const register = useCallback((payload: RegisterRequest) => authApi.register(payload), []);
  const value = useMemo(() => ({ user, isLoading, signIn, register, signOut, refresh }), [user, isLoading, signIn, register, signOut, refresh]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}

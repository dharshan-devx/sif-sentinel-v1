"use client";

import { useEffect, type ReactNode } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { LoadingState, ErrorState } from "@/components/states";
import { loginPath, safeRedirect } from "@/lib/auth";
import { useAuth } from "@/providers";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { status, refreshSession } = useAuth();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const router = useRouter();
  const next = safeRedirect(`${pathname}${searchParams.size ? `?${searchParams}` : ""}`);

  useEffect(() => {
    if (status === "unauthenticated") router.replace(loginPath(next));
  }, [next, router, status]);

  if (status === "loading" || status === "unauthenticated") return <main className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-7xl items-center px-4"><LoadingState label={status === "loading" ? "Checking your session" : "Taking you to sign in"} /></main>;
  if (status === "unavailable") return <main className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-2xl items-center px-4"><ErrorState title="Session check unavailable" error={new Error("We could not confirm your session. Your session has been retained.")} onRetry={() => void refreshSession()} /></main>;
  return <>{children}</>;
}

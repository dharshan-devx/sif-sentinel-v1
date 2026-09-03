"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { PageSkeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { useAuth } from "@/providers/auth-provider";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, status, initializationError, refresh } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  useEffect(() => {
    if (status === "unauthenticated") router.replace(`/login?next=${encodeURIComponent(pathname)}`);
  }, [pathname, router, status]);
  if (status === "loading") return <main className="p-6" aria-live="polite"><p className="mb-4 text-sm font-semibold text-slate-700">Loading session...</p><PageSkeleton /></main>;
  if (status === "unavailable") return <main className="p-6"><ErrorState error={new Error(initializationError ?? "We could not restore your session.")} retry={() => { void refresh(); }} /></main>;
  if (!user) return null;
  return <>{children}</>;
}

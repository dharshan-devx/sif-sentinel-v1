"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/providers/auth-provider";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  useEffect(() => {
    if (!isLoading && !user) router.replace(`/login?next=${encodeURIComponent(pathname)}`);
  }, [isLoading, pathname, router, user]);
  if (isLoading || !user) return <main className="p-6"><PageSkeleton /></main>;
  return <>{children}</>;
}

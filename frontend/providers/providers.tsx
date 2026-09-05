"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ApiError } from "@/lib/api";
import { AuthProvider } from "./auth-provider";

function shouldRetry(failureCount: number, error: unknown) {
  if (error instanceof ApiError && [401, 403, 404, 409, 422].includes(error.status)) return false;
  return failureCount < 2;
}

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        retry: shouldRetry,
        refetchOnWindowFocus: false,
        refetchOnReconnect: true,
      },
      mutations: { retry: false },
    },
  }));

  return <QueryClientProvider client={queryClient}><TooltipProvider><AuthProvider>{children}</AuthProvider></TooltipProvider></QueryClientProvider>;
}

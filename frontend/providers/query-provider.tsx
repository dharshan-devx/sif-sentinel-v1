"use client";

import { QueryClient, QueryClientProvider as Provider } from "@tanstack/react-query";
import { useState } from "react";

export function QueryClientProvider({ children }: { children: React.ReactNode }) {
  // Use state to ensure the client is instantiated exactly once per session
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute stale time default
            retry: 1, // Only retry once on failure to prevent long hangs
            refetchOnWindowFocus: false, // Prevent aggressive refetches on focus
          },
        },
      })
  );

  return <Provider client={queryClient}>{children}</Provider>;
}

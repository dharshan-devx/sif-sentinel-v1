"use client";

import { QueryClientProvider } from "@/providers/query-provider";
import { TooltipProvider } from "@/components/ui/tooltip";

export function AppProviders({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider>
      <TooltipProvider>
        {/* Future providers (AuthProvider, ThemeProvider, etc.) */}
        {children}
      </TooltipProvider>
    </QueryClientProvider>
  );
}

"use client";

import { useEffect } from "react";
import { ErrorState } from "@/components/ui/error-state";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Route Error Boundary caught:", error);
  }, [error]);

  return (
    <main className="flex min-h-[60vh] flex-col items-center justify-center p-4 sm:p-8">
      <div className="w-full max-w-2xl">
        <ErrorState
          title="Something went wrong"
          message="We encountered an issue loading this page."
          onRetry={reset}
        />
      </div>
    </main>
  );
}

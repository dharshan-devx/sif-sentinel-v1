"use client";

import { useEffect } from "react";
import { ErrorState } from "@/components/ui/error-state";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service if needed
    console.error("Global Error Boundary caught:", error);
  }, [error]);

  return (
    <html lang="en">
      <body>
        <main className="flex min-h-screen flex-col items-center justify-center bg-slate-50 p-4 sm:p-8">
          <div className="w-full max-w-2xl">
            <ErrorState
              title="A critical error occurred"
              message="The application crashed unexpectedly. We apologize for the inconvenience."
              onRetry={reset}
            />
          </div>
        </main>
      </body>
    </html>
  );
}

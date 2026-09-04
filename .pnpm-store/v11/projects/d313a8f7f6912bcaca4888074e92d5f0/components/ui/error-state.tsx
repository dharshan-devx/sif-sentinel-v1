import { AlertCircle, RefreshCcw } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface ErrorStateProps {
  title?: string;
  message?: string;
  error?: Error;
  requestId?: string | null;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = "Something went wrong",
  message = "We encountered an unexpected error while trying to process your request.",
  error,
  requestId,
  onRetry,
  className,
}: ErrorStateProps) {
  const displayMessage = error?.message || message;

  return (
    <div
      className={cn(
        "flex min-h-[400px] w-full flex-col items-center justify-center rounded-lg border border-red-100 bg-red-50/30 p-8 text-center",
        className
      )}
      role="alert"
    >
      <div className="mb-4 rounded-full bg-red-100 p-3">
        <AlertCircle className="h-8 w-8 text-red-600" aria-hidden="true" />
      </div>
      <h3 className="mb-2 text-lg font-semibold text-slate-900">{title}</h3>
      <p className="mb-6 max-w-md text-sm text-slate-600">{displayMessage}</p>
      
      {requestId && (
        <div className="mb-6 rounded-md bg-slate-100 px-3 py-2 text-xs font-mono text-slate-500">
          Request ID: {requestId}
        </div>
      )}

      {onRetry && (
        <Button onClick={onRetry} variant="outline" className="gap-2">
          <RefreshCcw className="h-4 w-4" />
          Try Again
        </Button>
      )}
    </div>
  );
}

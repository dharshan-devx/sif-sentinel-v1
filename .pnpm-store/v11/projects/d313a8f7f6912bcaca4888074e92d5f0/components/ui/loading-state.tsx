import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LoadingStateProps {
  text?: string;
  className?: string;
}

export function LoadingState({ text = "Loading...", className }: LoadingStateProps) {
  return (
    <div
      className={cn(
        "flex min-h-[400px] w-full flex-col items-center justify-center p-8 text-slate-500",
        className
      )}
      role="status"
      aria-live="polite"
    >
      <Loader2 className="mb-4 h-8 w-8 animate-spin text-slate-400" aria-hidden="true" />
      <p className="text-sm font-medium">{text}</p>
      <span className="sr-only">Loading</span>
    </div>
  );
}

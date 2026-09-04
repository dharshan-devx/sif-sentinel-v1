import { FolderOpen } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  title = "No data found",
  description = "There is nothing to display here right now.",
  icon = <FolderOpen className="h-10 w-10 text-slate-300" aria-hidden="true" />,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex min-h-[400px] w-full flex-col items-center justify-center rounded-lg border border-dashed border-slate-200 bg-slate-50 p-8 text-center",
        className
      )}
    >
      <div className="mb-4 rounded-full bg-slate-100 p-4">{icon}</div>
      <h3 className="mb-1 text-lg font-semibold text-slate-900">{title}</h3>
      <p className="mb-6 max-w-sm text-sm text-slate-500">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
}

import { ShieldAlert } from "lucide-react";
import { cn } from "@/lib/utils";

interface ForbiddenStateProps {
  title?: string;
  message?: string;
  className?: string;
}

export function ForbiddenState({
  title = "Access Denied",
  message = "You do not have permission to view this resource. If you believe this is a mistake, please contact your administrator.",
  className,
}: ForbiddenStateProps) {
  return (
    <div
      className={cn(
        "flex min-h-[400px] w-full flex-col items-center justify-center rounded-lg border border-orange-100 bg-orange-50/50 p-8 text-center",
        className
      )}
    >
      <div className="mb-4 rounded-full bg-orange-100 p-4">
        <ShieldAlert className="h-10 w-10 text-orange-600" aria-hidden="true" />
      </div>
      <h3 className="mb-2 text-xl font-bold text-slate-900">{title}</h3>
      <p className="max-w-md text-sm text-slate-600">{message}</p>
    </div>
  );
}

import { PanelLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import { Header } from "./header";

/** Structural shell only. Navigation and authorization are introduced in F2. */
export function AppShell({ children, className }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("min-h-screen bg-background", className)}><Header /><div className="flex"><aside className="hidden w-64 shrink-0 border-r border-border p-5 lg:block" aria-label="Future application navigation"><div className="flex items-center gap-2 text-sm font-medium text-muted-foreground"><PanelLeft className="size-4" aria-hidden="true" />Navigation arrives in F2</div></aside><main className="min-w-0 flex-1">{children}</main></div></div>;
}

import { LoaderCircle } from "lucide-react";
import { cn } from "@/lib/utils";
export function LoadingState({ label = "Loading", className }: { label?: string; className?: string }) { return <div className={cn("flex min-h-40 flex-col items-center justify-center gap-3 text-center text-sm text-muted-foreground", className)} role="status" aria-live="polite"><LoaderCircle className="size-5 animate-spin text-primary motion-reduce:animate-none" aria-hidden="true" /><span>{label}</span></div>; }

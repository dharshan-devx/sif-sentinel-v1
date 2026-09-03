import { cn } from "@/lib/utils/cn";
export function Spinner({ size = "md" }: { size?: "sm" | "md" }) { return <span aria-label="Loading" role="status" className={cn("inline-block animate-spin rounded-full border-2 border-current border-r-transparent motion-reduce:animate-none", size === "sm" ? "h-4 w-4" : "h-6 w-6")} />; }

import { cn } from "@/lib/utils/cn";
type BadgeTone = "neutral" | "info" | "success" | "warning" | "danger" | "critical";
const tones: Record<BadgeTone, string> = { neutral: "bg-slate-100 text-slate-700", info: "bg-sky-100 text-sky-800", success: "bg-emerald-100 text-emerald-800", warning: "bg-amber-100 text-amber-900", danger: "bg-red-100 text-red-800", critical: "bg-violet-100 text-violet-900" };
export function Badge({ children, tone = "neutral", className }: { children: React.ReactNode; tone?: BadgeTone; className?: string }) { return <span className={cn("inline-flex items-center rounded-full px-2.5 py-1 text-xs font-bold tracking-wide", tones[tone], className)}>{children}</span>; }

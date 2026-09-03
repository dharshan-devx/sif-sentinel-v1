import { cn } from "@/lib/utils/cn";
type StatusTone = "neutral" | "good" | "attention" | "critical";
const styles: Record<StatusTone, string> = { neutral: "bg-slate-400", good: "bg-emerald-600", attention: "bg-amber-500", critical: "bg-red-700" };
export function StatusIndicator({ label, tone = "neutral" }: { label: string; tone?: StatusTone }) { return <span className="inline-flex items-center gap-2 text-sm font-medium text-slate-700"><span aria-hidden="true" className={cn("h-2.5 w-2.5 rounded-full", styles[tone])} />{label}</span>; }

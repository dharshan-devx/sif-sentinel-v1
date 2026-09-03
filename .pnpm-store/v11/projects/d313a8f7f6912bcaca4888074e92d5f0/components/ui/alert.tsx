import { cn } from "@/lib/utils/cn";
type AlertTone = "info" | "success" | "warning" | "danger";
const styles: Record<AlertTone, string> = { info: "border-sky-200 bg-sky-50 text-sky-950", success: "border-emerald-200 bg-emerald-50 text-emerald-950", warning: "border-amber-200 bg-amber-50 text-amber-950", danger: "border-red-200 bg-red-50 text-red-950" };
export function Alert({ title, children, tone = "info" }: { title: string; children?: React.ReactNode; tone?: AlertTone }) { return <div role="alert" className={cn("rounded-lg border p-4 text-sm", styles[tone])}><p className="font-bold">{title}</p>{children && <div className="mt-1">{children}</div>}</div>; }

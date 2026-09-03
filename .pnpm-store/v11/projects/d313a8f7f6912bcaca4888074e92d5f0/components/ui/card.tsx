import { cn } from "@/lib/utils/cn";
export function Card({ children, className }: { children: React.ReactNode; className?: string }) { return <section className={cn("rounded-xl border border-slate-200 bg-white p-5 shadow-sm", className)}>{children}</section>; }
export function CardTitle({ children }: { children: React.ReactNode }) { return <h2 className="text-base font-bold text-slate-950">{children}</h2>; }

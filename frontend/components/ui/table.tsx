import { cn } from "@/lib/utils/cn";
export function Table({ children, className, label }: { children: React.ReactNode; className?: string; label: string }) { return <div className="overflow-x-auto"><table aria-label={label} className={cn("w-full border-collapse text-left text-sm", className)}>{children}</table></div>; }
export function TableHead({ children }: { children: React.ReactNode }) { return <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-600">{children}</thead>; }
export function TableCell({ children, header = false }: { children: React.ReactNode; header?: boolean }) { const Cell = header ? "th" : "td"; return <Cell className="px-4 py-3 align-middle">{children}</Cell>; }

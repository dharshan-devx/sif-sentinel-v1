import { cn } from "@/lib/utils/cn";
export function Skeleton({ className }: { className?: string }) { return <div aria-hidden="true" className={cn("animate-pulse rounded bg-slate-200 motion-reduce:animate-none", className)} />; }
export function PageSkeleton() { return <div className="space-y-6"><Skeleton className="h-8 w-64" /><div className="grid gap-4 md:grid-cols-3">{[1, 2, 3].map((item) => <Skeleton key={item} className="h-32" />)}</div><Skeleton className="h-72" /></div>; }
export function TableSkeleton({ rows = 5 }: { rows?: number }) { return <div className="space-y-3">{Array.from({ length: rows }, (_, index) => <Skeleton key={index} className="h-12 w-full" />)}</div>; }

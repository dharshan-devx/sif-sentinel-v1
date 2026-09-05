import { cn } from "@/lib/utils";

export function PageContainer({ className, children }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8", className)}>{children}</div>;
}

export function SectionContainer({ className, children }: React.HTMLAttributes<HTMLElement>) {
  return <section className={cn("py-12 sm:py-16 lg:py-20", className)}>{children}</section>;
}

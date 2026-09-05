import type { ReactNode } from "react";
import Link from "next/link";
import { ShieldCheck } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function AuthCard({ title, description, children, footer }: { title: string; description: string; children: ReactNode; footer: ReactNode }) {
  return <main className="grid min-h-screen place-items-center bg-muted/35 px-4 py-8"><Card className="w-full max-w-md"><CardHeader className="space-y-4"><Link href="/" className="inline-flex w-fit items-center gap-2 rounded-md font-semibold tracking-tight focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"><span className="grid size-8 place-items-center rounded-md bg-primary text-primary-foreground"><ShieldCheck className="size-4" aria-hidden="true" /></span>SIF <span className="text-primary">SENTINEL</span></Link><div><CardTitle className="text-2xl">{title}</CardTitle><CardDescription className="mt-2 leading-6">{description}</CardDescription></div></CardHeader><CardContent>{children}<div className="mt-6 border-t border-border pt-5 text-center text-sm text-muted-foreground">{footer}</div></CardContent></Card></main>;
}

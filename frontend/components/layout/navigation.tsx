"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";
import { navigationForRole } from "@/lib/navigation";
import type { AuthUser } from "@/types/api";

export function Brand() { return <Link href="/dashboard" className="inline-flex min-h-10 items-center gap-2 rounded-md font-semibold tracking-tight focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"><span className="grid size-8 place-items-center rounded-md bg-primary text-primary-foreground"><ShieldCheck className="size-4" aria-hidden="true" /></span><span>SIF <span className="text-primary">SENTINEL</span></span></Link>; }
export function NavigationLinks({ user, onNavigate }: { user: AuthUser; onNavigate?: () => void }) { const pathname = usePathname(); return <nav aria-label="Primary navigation" className="mt-8 space-y-1">{navigationForRole(user.role).map(({ href, label, icon: Icon }) => { const active = pathname === href; return <Link key={href} href={href} onClick={onNavigate} aria-current={active ? "page" : undefined} className={cn("flex min-h-10 items-center gap-3 rounded-md px-3 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring", active ? "bg-secondary text-secondary-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground")}><Icon className="size-4" aria-hidden="true" />{label}</Link>; })}</nav>; }

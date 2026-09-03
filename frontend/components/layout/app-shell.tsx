"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dropdown } from "@/components/ui/dropdown";
import { cn } from "@/lib/utils/cn";
import { navigationItems } from "@/lib/constants/roles";
import { useAuth } from "@/providers/auth-provider";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const { user, signOut } = useAuth();
  const navigation = navigationItems.filter((item) => user && item.roles.includes(user.role));
  const leaveSession = () => { signOut(); router.replace("/login"); };
  return <div className="min-h-screen bg-slate-50 text-slate-950">
    <aside id="primary-navigation" aria-label="Primary navigation" className={cn("fixed inset-y-0 left-0 z-30 w-72 border-r border-slate-200 bg-slate-950 p-4 text-slate-100 transition-transform md:translate-x-0", mobileOpen ? "translate-x-0" : "-translate-x-full")}>
      <div className="flex items-center justify-between border-b border-slate-700 pb-4"><Link href="/dashboard" className="font-bold tracking-tight">SIF SENTINEL</Link><Badge tone="info">Safety signals</Badge></div>
      <nav className="mt-5 space-y-1">{navigation.map((item) => <Link onClick={() => setMobileOpen(false)} key={item.href} href={item.href} className={cn("block rounded-md px-3 py-2.5 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400", pathname === item.href ? "bg-sky-700 text-white" : "text-slate-300 hover:bg-slate-800 hover:text-white")}>{item.label}</Link>)}</nav>
      <p className="absolute inset-x-4 bottom-5 border-t border-slate-700 pt-4 text-xs leading-5 text-slate-400">Decision support only. Human review remains authoritative.</p>
    </aside>
    {mobileOpen && <button aria-label="Close navigation" className="fixed inset-0 z-20 bg-slate-950/40 md:hidden" onClick={() => setMobileOpen(false)} />}
    <div className="md:pl-72"><header className="sticky top-0 z-10 flex min-h-16 items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur md:px-8"><Button variant="ghost" className="md:hidden" type="button" aria-expanded={mobileOpen} aria-controls="primary-navigation" onClick={() => setMobileOpen(true)}>Menu</Button><div className="hidden text-sm text-slate-600 md:block">Workplace safety decision support</div><Dropdown label={user?.full_name ?? "Account"}><div className="px-3 py-2 text-xs text-slate-600">{user?.email}<br /><span className="font-bold">{user?.role}</span></div><button type="button" className="w-full rounded px-3 py-2 text-left text-sm font-semibold hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-sky-600" onClick={leaveSession}>End session</button></Dropdown></header><main className="mx-auto w-full max-w-7xl p-4 md:p-8">{children}</main></div>
  </div>;
}

"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dropdown } from "@/components/ui/dropdown";
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from "@/components/ui/sheet";
import { Menu } from "lucide-react";
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

  // Close mobile nav when pathname changes
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { setMobileOpen(false); }, [pathname]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      {/* Desktop Sidebar */}
      <aside aria-label="Primary navigation" className="hidden md:block fixed inset-y-0 left-0 w-72 border-r border-slate-800 bg-slate-950 p-4 text-slate-100">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <Link href="/dashboard" className="font-bold tracking-tight text-white">SIF SENTINEL</Link>
          <Badge tone="info">Safety signals</Badge>
        </div>
        <nav className="mt-5 space-y-1">
          {navigation.map((item) => (
            <Link 
              key={item.href} 
              href={item.href} 
              className={cn(
                "block rounded-md px-3 py-2.5 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400", 
                pathname === item.href ? "bg-sky-700 text-white" : "text-slate-300 hover:bg-slate-800 hover:text-white"
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <p className="absolute inset-x-4 bottom-5 border-t border-slate-800 pt-4 text-xs leading-5 text-slate-400">
          Decision support only. Human review remains authoritative.
        </p>
      </aside>

      <div className="md:pl-72">
        <header className="sticky top-0 z-10 flex min-h-16 items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur md:px-8">
          <div className="flex items-center md:hidden">
            <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" aria-label="Open menu" className="px-2">
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent className="bg-slate-950 text-slate-100 border-r-slate-800 p-4 w-72">
                <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
                <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                  <Link href="/dashboard" className="font-bold tracking-tight text-white" onClick={() => setMobileOpen(false)}>SIF SENTINEL</Link>
                  <Badge tone="info">Safety signals</Badge>
                </div>
                <nav className="mt-5 space-y-1">
                  {navigation.map((item) => (
                    <Link 
                      key={item.href} 
                      href={item.href} 
                      onClick={() => setMobileOpen(false)}
                      className={cn(
                        "block rounded-md px-3 py-2.5 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400", 
                        pathname === item.href ? "bg-sky-700 text-white" : "text-slate-300 hover:bg-slate-800 hover:text-white"
                      )}
                    >
                      {item.label}
                    </Link>
                  ))}
                </nav>
              </SheetContent>
            </Sheet>
          </div>
          
          <div className="hidden text-sm text-slate-600 md:block">
            Workplace safety decision support
          </div>
          
          <Dropdown label={user?.full_name ?? "Account"}>
            <div className="px-3 py-2 text-xs text-slate-600">
              {user?.email}<br />
              <span className="font-bold">{user?.role}</span>
            </div>
            <button 
              type="button" 
              className="w-full rounded px-3 py-2 text-left text-sm font-semibold hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-sky-600" 
              onClick={leaveSession}
            >
              End session
            </button>
          </Dropdown>
        </header>
        
        <main className="mx-auto w-full max-w-7xl p-4 md:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}

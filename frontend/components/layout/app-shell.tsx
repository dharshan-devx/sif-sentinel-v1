"use client";
import { Menu } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { useAuth } from "@/providers";
import { Brand, NavigationLinks } from "./navigation";
import { UserSessionMenu } from "./user-session-menu";

/** Authenticated application shell with persistent sidebar, mobile sheet navigation, and user menu. */
export function AppShell({ children, className, pageTitle = "Dashboard" }: React.HTMLAttributes<HTMLDivElement> & { pageTitle?: string }) {
  const { user } = useAuth();
  if (!user) return null;
  return (
    <div className={cn("min-h-screen", className)}>
      <aside className="glass-panel fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-border/50 p-5 lg:block">
        <Brand />
        <NavigationLinks user={user} />
        <div className="absolute inset-x-5 bottom-5">
          <UserSessionMenu />
        </div>
      </aside>
      <div className="min-h-screen lg:pl-64 flex flex-col">
        <header className="glass-header sticky top-0 z-20 flex min-h-16 items-center justify-between px-4 sm:px-6 shadow-sm">
          <div className="flex items-center gap-3">
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Open navigation">
                  <Menu className="size-5" aria-hidden="true" />
                </Button>
              </SheetTrigger>
              <SheetContent>
                <SheetHeader>
                  <SheetTitle><Brand /></SheetTitle>
                </SheetHeader>
                <NavigationLinks user={user} />
              </SheetContent>
            </Sheet>
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">SIF Sentinel</p>
              <h1 className="text-lg font-bold tracking-tight">{pageTitle}</h1>
            </div>
          </div>
          <div className="lg:hidden">
            <UserSessionMenu />
          </div>
        </header>
        <main className="flex-1 min-w-0">
          {children}
        </main>
      </div>
    </div>
  );
}

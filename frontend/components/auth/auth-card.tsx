import type { ReactNode } from "react";
import Link from "next/link";
import { ShieldCheck } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import * as motion from "framer-motion/client";

export function AuthCard({ title, description, children, footer }: { title: string; description: string; children: ReactNode; footer: ReactNode }) {
  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden py-12 px-4 sm:px-6 lg:px-8">
      {/* Decorative background blobs */}
      <div className="absolute top-1/4 -left-20 h-72 w-72 rounded-full bg-primary/20 blur-3xl opacity-50 animate-pulse"></div>
      <div className="absolute bottom-1/4 -right-20 h-72 w-72 rounded-full bg-teal-400/20 blur-3xl opacity-50 animate-pulse" style={{ animationDelay: "1s" }}></div>
      
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="w-full max-w-md z-10"
      >
        <Card className="glass-card border-none shadow-2xl">
          <CardHeader className="space-y-4">
            <Link href="/" className="group inline-flex w-fit items-center gap-2 rounded-md font-semibold tracking-tight focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
              <div className="grid size-9 place-items-center rounded-xl bg-gradient-to-br from-primary to-primary/80 text-primary-foreground shadow-sm transition-transform group-hover:scale-105">
                <ShieldCheck className="size-5" aria-hidden="true" />
              </div>
              <span className="text-lg">SIF <span className="text-primary font-bold">SENTINEL</span></span>
            </Link>
            <div>
              <CardTitle className="text-2xl font-bold tracking-tight">{title}</CardTitle>
              <CardDescription className="mt-2 text-base">{description}</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            {children}
            <div className="mt-8 border-t border-border/50 pt-6 text-center text-sm text-muted-foreground">
              {footer}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </main>
  );
}

"use client";
import Link from "next/link";
import { ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageContainer } from "./page-container";
import { useAuth } from "@/providers";
import { motion } from "framer-motion";

/**
 * Public-page top header. Auth-aware: shows a Dashboard link for authenticated
 * users, or a Sign in link for unauthenticated / unknown state.
 */
export function Header() {
  const { status } = useAuth();

  return (
    <motion.header 
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      className="sticky top-0 z-50 glass-header"
    >
      <PageContainer className="flex min-h-16 items-center justify-between gap-4">
        <Link
          href="/"
          className="group inline-flex min-h-11 items-center gap-2 rounded-md font-semibold tracking-tight focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <div className="grid size-9 place-items-center rounded-xl bg-gradient-to-br from-primary to-primary/80 text-primary-foreground shadow-sm transition-transform group-hover:scale-105">
            <ShieldCheck className="size-5" aria-hidden="true" />
          </div>
          <span className="text-lg">
            SIF <span className="text-primary font-bold">SENTINEL</span>
          </span>
        </Link>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          {status === "authenticated" ? (
            <Button asChild variant="default" size="sm" className="rounded-full px-6 shadow-md hover:shadow-lg transition-all">
              <Link href="/dashboard">Dashboard</Link>
            </Button>
          ) : (
            <div className="flex items-center gap-2">
              <Button asChild variant="ghost" size="sm" className="rounded-full px-4 hover:bg-black/5">
                <Link href="/login">Sign in</Link>
              </Button>
              <Button asChild variant="default" size="sm" className="rounded-full px-6 shadow-md hover:shadow-lg transition-all">
                <Link href="/register">Get Started</Link>
              </Button>
            </div>
          )}
        </motion.div>
      </PageContainer>
    </motion.header>
  );
}

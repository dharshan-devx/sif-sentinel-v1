"use client";
import { useEffect } from "react";
import { ErrorState } from "@/components/states";
export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) { useEffect(() => { /* Error reporting is intentionally added only with approved telemetry. */ }, [error]); return <main className="mx-auto flex min-h-screen max-w-2xl items-center px-4"><ErrorState error={error} onRetry={reset} title="We could not load this page" /></main>; }

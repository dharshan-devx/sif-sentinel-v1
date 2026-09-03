"use client";
import { ErrorState } from "@/components/ui/error-state";
export default function GlobalError({ error, reset }: { error: Error; reset: () => void }) { return <main className="mx-auto max-w-2xl p-6"><ErrorState error={error} retry={reset} /></main>; }

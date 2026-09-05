import Link from "next/link";
import { SearchX } from "lucide-react";
import { Button } from "@/components/ui/button";
export default function NotFound() { return <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center px-4 text-center"><SearchX className="size-10 text-muted-foreground" aria-hidden="true" /><p className="mt-6 text-sm font-semibold text-primary">404</p><h1 className="mt-2 text-3xl font-semibold tracking-tight">Page not found</h1><p className="mt-3 text-muted-foreground">The page you requested is not part of this workspace.</p><Button asChild className="mt-6"><Link href="/">Return to SIF Sentinel</Link></Button></main>; }

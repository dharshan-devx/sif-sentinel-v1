import Link from "next/link";
import { EmptyState } from "@/components/ui/empty-state";
export default function NotFound() { return <main className="mx-auto max-w-2xl p-6"><EmptyState title="Page not found" description="The route is not available in SIF Sentinel." action={<Link className="font-bold text-sky-800 underline" href="/dashboard">Return to safety overview</Link>} /></main>; }

import Link from "next/link";
import { ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageContainer } from "./page-container";

export function Header() {
  return (
    <header className="border-b border-border bg-background/95">
      <PageContainer className="flex min-h-16 items-center justify-between gap-4">
        <Link href="/" className="inline-flex min-h-11 items-center gap-2 rounded-md font-semibold tracking-tight focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
          <span className="grid size-8 place-items-center rounded-md bg-primary text-primary-foreground"><ShieldCheck className="size-4" aria-hidden="true" /></span>
          <span>SIF <span className="text-primary">SENTINEL</span></span>
        </Link>
        <Button variant="outline" size="sm" disabled aria-label="Application access is planned for the next release">
          Workspace access <span className="hidden sm:inline">— coming next</span>
        </Button>
      </PageContainer>
    </header>
  );
}

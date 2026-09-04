import { EmptyState } from "@/components/ui/empty-state";
import { buttonVariants } from "@/components/ui/button";
import Link from "next/link";
import { SearchX } from "lucide-react";

export default function NotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-slate-50 p-4 sm:p-8">
      <div className="w-full max-w-xl">
        <EmptyState
          icon={<SearchX className="h-10 w-10 text-slate-400" />}
          title="Page Not Found"
          description="The resource you are looking for does not exist or has been moved."
          action={
            <Link href="/" className={buttonVariants({ variant: "default" })}>Return to Home</Link>
          }
        />
      </div>
    </main>
  );
}

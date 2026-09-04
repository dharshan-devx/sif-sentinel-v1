import { LoadingState } from "@/components/ui/loading-state";

export default function Loading() {
  return (
    <main className="flex min-h-screen items-center justify-center">
      <LoadingState text="Loading page..." />
    </main>
  );
}

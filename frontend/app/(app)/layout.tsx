import type { ReactNode } from "react";
import { ProtectedRoute } from "@/components/auth";

export default function AppLayout({ children }: { children: ReactNode }) {
  return <ProtectedRoute>{children}</ProtectedRoute>;
}

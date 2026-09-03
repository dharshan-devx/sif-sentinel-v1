import { AppShell } from "@/components/layout/app-shell";
import { AuthGate } from "@/components/layout/auth-gate";
export default function DashboardLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <AuthGate><AppShell>{children}</AppShell></AuthGate>; }

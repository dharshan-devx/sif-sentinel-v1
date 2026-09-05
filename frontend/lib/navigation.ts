import type { UserRole } from "@/types/api";
import { LayoutDashboard } from "lucide-react";

export interface NavigationItem { label: string; href: string; icon: typeof LayoutDashboard; roles: UserRole[]; }

/** Only implemented routes appear here. Future capabilities are intentionally not represented as links. */
export const navigationItems: NavigationItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard, roles: ["ADMIN", "HSE_MANAGER", "HSE_ANALYST", "REVIEWER", "VIEWER"] },
];

export function navigationForRole(role: UserRole | undefined): NavigationItem[] {
  return role ? navigationItems.filter((item) => item.roles.includes(role)) : [];
}

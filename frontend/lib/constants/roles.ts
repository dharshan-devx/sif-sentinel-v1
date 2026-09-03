import type { UserRole } from "@/types/api";

export type Capability = "report:write" | "report:delete" | "site:manage" | "review:decide" | "intervention:decide" | "precursor:rebuild" | "model:read";

const capabilityRoles: Record<Capability, UserRole[]> = {
  "report:write": ["ADMIN", "HSE_MANAGER", "HSE_ANALYST", "REVIEWER"],
  "report:delete": ["ADMIN", "HSE_MANAGER"],
  "site:manage": ["ADMIN", "HSE_MANAGER"],
  "review:decide": ["ADMIN", "HSE_MANAGER", "REVIEWER"],
  "intervention:decide": ["ADMIN", "HSE_MANAGER", "REVIEWER"],
  "precursor:rebuild": ["ADMIN", "HSE_MANAGER", "HSE_ANALYST"],
  "model:read": ["ADMIN", "HSE_MANAGER", "HSE_ANALYST"],
};

export function hasCapability(role: UserRole | undefined, capability: Capability): boolean {
  return role !== undefined && capabilityRoles[capability].includes(role);
}

export interface NavigationItem { href: string; label: string; roles: UserRole[] }

const allRoles: UserRole[] = ["ADMIN", "HSE_MANAGER", "HSE_ANALYST", "REVIEWER", "VIEWER"];
export const navigationItems: NavigationItem[] = [
  { href: "/dashboard", label: "Safety overview", roles: allRoles },
  { href: "/reports", label: "Reports", roles: allRoles },
  { href: "/reviews", label: "Human reviews", roles: ["ADMIN", "HSE_MANAGER", "REVIEWER"] },
  { href: "/interventions", label: "Recommendations", roles: allRoles },
  { href: "/precursors", label: "Precursors", roles: allRoles },
  { href: "/risk", label: "Risk signals", roles: allRoles },
  { href: "/rules", label: "Life-Saving Rules", roles: allRoles },
  { href: "/models", label: "Model observability", roles: ["ADMIN", "HSE_MANAGER", "HSE_ANALYST"] },
];

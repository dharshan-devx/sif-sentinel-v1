"use client";
import { hasCapability, type Capability } from "@/lib/constants/roles";
import { useAuth } from "@/providers/auth-provider";
export function useRoleGuard(capability: Capability): boolean { const { user } = useAuth(); return hasCapability(user?.role, capability); }

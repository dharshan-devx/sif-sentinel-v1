"use client";

import type { ReactNode } from "react";
import { ResponsiveContainer } from "recharts";

/** Shared, accessible container for future Recharts visualizations. */
export function ChartFrame({ children, label }: { children: ReactNode; label: string }) {
  return <div role="img" aria-label={label} className="h-72 w-full"><ResponsiveContainer width="100%" height="100%">{children as React.ReactElement}</ResponsiveContainer></div>;
}

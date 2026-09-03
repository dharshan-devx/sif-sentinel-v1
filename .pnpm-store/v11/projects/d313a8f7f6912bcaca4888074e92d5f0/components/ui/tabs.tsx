"use client";

import { cn } from "@/lib/utils/cn";
export interface Tab { id: string; label: string; disabled?: boolean }
export function Tabs({ tabs, activeId, onChange }: { tabs: Tab[]; activeId: string; onChange: (id: string) => void }) { return <div role="tablist" aria-label="Content sections" className="flex gap-1 border-b border-slate-200">{tabs.map((tab) => <button key={tab.id} role="tab" type="button" aria-selected={tab.id === activeId} disabled={tab.disabled} onClick={() => onChange(tab.id)} className={cn("border-b-2 px-3 py-2 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-sky-600 disabled:opacity-50", tab.id === activeId ? "border-sky-700 text-sky-800" : "border-transparent text-slate-600 hover:text-slate-950")}>{tab.label}</button>)}</div>; }

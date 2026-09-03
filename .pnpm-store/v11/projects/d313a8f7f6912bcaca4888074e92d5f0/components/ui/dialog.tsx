"use client";
import { useEffect, useRef, type ReactNode } from "react";
import { Button } from "@/components/ui/button";
export function Dialog({ open, title, children, onClose }: { open: boolean; title: string; children: ReactNode; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => { const dialog = ref.current; if (!dialog) return; if (open && !dialog.open) dialog.showModal(); if (!open && dialog.open) dialog.close(); }, [open]);
  return <dialog ref={ref} aria-labelledby="dialog-title" onCancel={(event) => { event.preventDefault(); onClose(); }} className="w-[min(32rem,calc(100%-2rem)] rounded-xl border border-slate-200 p-0 shadow-2xl backdrop:bg-slate-950/40"><div className="p-6"><div className="mb-4 flex items-start justify-between gap-4"><h2 id="dialog-title" className="text-lg font-bold">{title}</h2><Button variant="ghost" type="button" aria-label="Close dialog" onClick={onClose}>Close</Button></div>{children}</div></dialog>;
}

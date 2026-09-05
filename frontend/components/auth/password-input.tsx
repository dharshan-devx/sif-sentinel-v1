"use client";
import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function PasswordInput({ id, invalid, describedBy, value, onChange, disabled }: { id: string; invalid?: boolean; describedBy?: string; value: string; onChange: (value: string) => void; disabled?: boolean }) {
  const [visible, setVisible] = useState(false);
  return <div className="relative"><Input id={id} name="password" type={visible ? "text" : "password"} autoComplete="current-password" value={value} onChange={(event) => onChange(event.target.value)} aria-invalid={invalid || undefined} aria-describedby={describedBy} disabled={disabled} className="pr-11" /><Button type="button" variant="ghost" size="icon" className="absolute right-0 top-0 h-10 w-10" aria-label={visible ? "Hide password" : "Show password"} onClick={() => setVisible((current) => !current)} disabled={disabled}>{visible ? <EyeOff className="size-4" aria-hidden="true" /> : <Eye className="size-4" aria-hidden="true" />}</Button></div>;
}

"use client";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, authApi } from "@/lib/api";
import { AuthCard } from "@/components/auth/auth-card";
import { PasswordInput } from "@/components/auth/password-input";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState(""); const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({}); const [error, setError] = useState<string | null>(null); const [pending, setPending] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const errors: Record<string, string> = {};
    if (!fullName.trim()) errors.fullName = "Enter your full name.";
    if (!email.trim()) errors.email = "Enter your email address.";
    if (password.length < 12) errors.password = "Use at least 12 characters.";
    setFieldErrors(errors); setError(null); if (Object.keys(errors).length) return;
    setPending(true);
    try { await authApi.register({ full_name: fullName.trim(), email: email.trim(), password }); router.replace("/login?registered=1"); }
    catch (cause) { setError(cause instanceof ApiError ? cause.message : "We could not create your account. Please try again."); }
    finally { setPending(false); }
  }
  return <AuthCard title="Create your account" description="New registrations receive Viewer access. Elevated roles are provisioned outside this form." footer={<>Already have an account? <Link href="/login" className="font-semibold text-primary underline-offset-4 hover:underline">Sign in</Link></>}><form className="space-y-5" onSubmit={submit} noValidate><div className="space-y-2"><Label htmlFor="full-name">Full name</Label><Input id="full-name" autoComplete="name" value={fullName} onChange={(event) => setFullName(event.target.value)} aria-invalid={Boolean(fieldErrors.fullName) || undefined} aria-describedby={fieldErrors.fullName ? "full-name-error" : undefined} disabled={pending} />{fieldErrors.fullName ? <p id="full-name-error" className="text-sm text-destructive">{fieldErrors.fullName}</p> : null}</div><div className="space-y-2"><Label htmlFor="register-email">Email address</Label><Input id="register-email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} aria-invalid={Boolean(fieldErrors.email) || undefined} aria-describedby={fieldErrors.email ? "register-email-error" : undefined} disabled={pending} />{fieldErrors.email ? <p id="register-email-error" className="text-sm text-destructive">{fieldErrors.email}</p> : null}</div><div className="space-y-2"><Label htmlFor="register-password">Password</Label><PasswordInput id="register-password" value={password} onChange={setPassword} invalid={Boolean(fieldErrors.password)} describedBy={fieldErrors.password ? "register-password-error" : undefined} disabled={pending} />{fieldErrors.password ? <p id="register-password-error" className="text-sm text-destructive">{fieldErrors.password}</p> : <p className="text-xs text-muted-foreground">Use 12–128 characters.</p>}</div>{error ? <Alert variant="destructive" aria-live="assertive"><AlertDescription>{error}</AlertDescription></Alert> : null}<Button type="submit" className="w-full" disabled={pending}>{pending ? "Creating account…" : "Create Viewer account"}</Button></form></AuthCard>;
}

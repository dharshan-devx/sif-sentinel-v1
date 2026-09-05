"use client";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LoadingState } from "@/components/states";
import { ApiError } from "@/lib/api";
import { safeRedirect } from "@/lib/auth";
import { useAuth } from "@/providers";
import { AuthCard } from "@/components/auth/auth-card";
import { PasswordInput } from "@/components/auth/password-input";

export default function LoginPage() {
  const { status, signIn } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [pending, setPending] = useState(false);
  const destination = safeRedirect(searchParams.get("next"));

  useEffect(() => { if (status === "authenticated") router.replace(destination); }, [destination, router, status]);
  if (status === "loading") return <LoadingState label="Checking your session" className="min-h-screen" />;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const errors: Record<string, string> = {};
    if (!email.trim()) errors.email = "Enter your email address.";
    if (!password) errors.password = "Enter your password.";
    setFieldErrors(errors); setError(null);
    if (Object.keys(errors).length) return;
    setPending(true);
    try { await signIn({ email: email.trim(), password }); router.replace(destination); }
    catch (cause) { setError(cause instanceof ApiError ? cause.message : "We could not sign you in. Please try again."); }
    finally { setPending(false); }
  }

  return <AuthCard title="Welcome back" description="Sign in to continue to your safety workspace." footer={<>Need an account? <Link href="/register" className="font-semibold text-primary underline-offset-4 hover:underline">Register</Link></>}><form className="space-y-5" onSubmit={submit} noValidate><div className="space-y-2"><Label htmlFor="email">Email address</Label><Input id="email" name="email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} aria-invalid={Boolean(fieldErrors.email) || undefined} aria-describedby={fieldErrors.email ? "email-error" : undefined} disabled={pending} />{fieldErrors.email ? <p id="email-error" className="text-sm text-destructive">{fieldErrors.email}</p> : null}</div><div className="space-y-2"><Label htmlFor="password">Password</Label><PasswordInput id="password" value={password} onChange={setPassword} invalid={Boolean(fieldErrors.password)} describedBy={fieldErrors.password ? "password-error" : undefined} disabled={pending} />{fieldErrors.password ? <p id="password-error" className="text-sm text-destructive">{fieldErrors.password}</p> : null}</div>{searchParams.get("registered") === "1" ? <Alert><AlertDescription>Your account is ready. New accounts are Viewer accounts.</AlertDescription></Alert> : null}{error ? <Alert variant="destructive" aria-live="assertive"><AlertDescription>{error}</AlertDescription></Alert> : null}<Button type="submit" className="w-full" disabled={pending}>{pending ? "Signing in…" : "Sign in"}</Button></form></AuthCard>;
}

"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { isApiClientError } from "@/lib/api/client";
import { useAuth } from "@/providers/auth-provider";

function safeNext(value: string | null): string { return value?.startsWith("/") && !value.startsWith("//") ? value : "/dashboard"; }
export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const [pending, setPending] = useState(false); const [error, setError] = useState<string | null>(null);
  const { signIn, register } = useAuth(); const router = useRouter(); const params = useSearchParams();
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setError(null); setPending(true); const data = new FormData(event.currentTarget);
    try {
      const email = String(data.get("email") ?? ""); const password = String(data.get("password") ?? "");
      if (mode === "login") { await signIn({ email, password }); router.replace(safeNext(params.get("next"))); }
      else { await register({ email, password, full_name: String(data.get("full_name") ?? "") }); router.replace("/login?registered=1"); }
    } catch (cause) { setError(isApiClientError(cause) ? cause.message : "We could not complete that request."); }
    finally { setPending(false); }
  };
  const registerMode = mode === "register";
  return <Card className="w-full max-w-md"><h1 className="text-2xl font-bold">{registerMode ? "Create an account" : "Sign in"}</h1><p className="mt-2 text-sm text-slate-600">{registerMode ? "New accounts have viewer access until provisioned by an administrator." : "Use your SIF Sentinel account to view safety signals."}</p>{error && <div className="mt-4"><Alert title={error} tone="danger" /></div>}<form className="mt-6 space-y-4" onSubmit={submit}>{registerMode && <label className="block text-sm font-semibold">Full name<Input className="mt-1" name="full_name" autoComplete="name" required maxLength={255} /></label>}<label className="block text-sm font-semibold">Email<Input className="mt-1" name="email" type="email" autoComplete="email" required /></label><label className="block text-sm font-semibold">Password<Input className="mt-1" name="password" type="password" autoComplete={registerMode ? "new-password" : "current-password"} minLength={registerMode ? 12 : 1} maxLength={128} required /></label><Button className="w-full" type="submit" pending={pending}>{registerMode ? "Create account" : "Sign in"}</Button></form><p className="mt-5 text-center text-sm text-slate-600">{registerMode ? <>Already have an account? <Link className="font-bold text-sky-800 underline" href="/login">Sign in</Link></> : <>Need an account? <Link className="font-bold text-sky-800 underline" href="/register">Register</Link></>}</p></Card>;
}

"use client";
import { useState } from "react";
import { LogOut, UserRound } from "lucide-react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/providers";

export function UserSessionMenu() {
  const { user, endSession } = useAuth();
  const [open, setOpen] = useState(false);
  if (!user) return null;
  return <Dialog open={open} onOpenChange={setOpen}><DialogTrigger asChild><Button variant="ghost" className="h-auto max-w-[12rem] justify-start px-2 text-left"><span className="grid size-8 shrink-0 place-items-center rounded-full bg-secondary text-secondary-foreground"><UserRound className="size-4" aria-hidden="true" /></span><span className="min-w-0"><span className="block truncate text-sm">{user.full_name}</span><span className="block truncate text-xs font-normal text-muted-foreground">{user.role.replaceAll("_", " ")}</span></span></Button></DialogTrigger><DialogContent><DialogHeader><DialogTitle>Session</DialogTitle><DialogDescription>Signed in as {user.email}</DialogDescription></DialogHeader><div className="rounded-lg border border-border bg-muted/30 p-3"><p className="text-sm font-medium">{user.full_name}</p><Badge variant="secondary" className="mt-2">{user.role.replaceAll("_", " ")}</Badge></div><Button variant="outline" onClick={() => { setOpen(false); endSession(); }}><LogOut className="size-4" aria-hidden="true" />End Session</Button><p className="text-xs text-muted-foreground">This clears this browser session. It does not revoke a server token.</p></DialogContent></Dialog>;
}

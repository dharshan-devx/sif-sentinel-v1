import { AppShell, PageContainer } from "@/components/layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ProtectedRoute } from "@/components/auth";

export default function DashboardPlaceholder() { return <ProtectedRoute><AppShell pageTitle="Dashboard"><PageContainer className="py-8 sm:py-10"><Card className="max-w-2xl"><CardHeader><CardTitle>Workspace ready</CardTitle><CardDescription>The operational dashboard is introduced in F3.</CardDescription></CardHeader><CardContent className="text-sm leading-6 text-muted-foreground">Your account and secure application shell are active. No safety metrics or operational data are displayed in this foundation phase.</CardContent></Card></PageContainer></AppShell></ProtectedRoute>; }

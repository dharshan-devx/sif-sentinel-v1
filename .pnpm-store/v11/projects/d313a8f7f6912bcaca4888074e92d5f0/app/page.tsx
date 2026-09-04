import { ShieldAlert, Activity, Users } from "lucide-react";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 w-full border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="container mx-auto flex h-16 items-center justify-between px-4 sm:px-8">
          <div className="flex items-center gap-2 font-bold text-slate-900 tracking-tight">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-slate-900 text-white">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <span className="text-xl">SIF Sentinel</span>
          </div>
          <nav className="flex items-center gap-4">
            {/* Future auth buttons will go here in F2 */}
            <Button variant="ghost" className="text-slate-600">Documentation</Button>
            <Link href="/login" className={buttonVariants({ variant: "default" })}>Sign In</Link>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <section className="bg-slate-900 py-24 text-white sm:py-32">
          <div className="container mx-auto px-4 text-center sm:px-8">
            <div className="mx-auto max-w-3xl">
              <h1 className="mb-6 text-4xl font-extrabold tracking-tight sm:text-6xl">
                Workplace Safety Decision Support
              </h1>
              <p className="mb-10 text-lg text-slate-300 sm:text-xl">
                The operations platform for managing Serious Injury and Fatality (SIF) precursors, predictive reporting, and incident response.
              </p>
              <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
                <Button size="lg" className="h-12 w-full bg-white text-slate-900 hover:bg-slate-100 sm:w-auto">
                  Get Started
                </Button>
                <Button size="lg" variant="outline" className="h-12 w-full border-slate-700 bg-slate-800 text-white hover:bg-slate-700 sm:w-auto">
                  Learn More
                </Button>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20">
          <div className="container mx-auto px-4 sm:px-8">
            <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
              <Card>
                <CardHeader>
                  <Activity className="mb-2 h-8 w-8 text-blue-600" />
                  <CardTitle>Real-time Monitoring</CardTitle>
                  <CardDescription>Track incidents and near-misses as they happen across all your facilities.</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-600">
                    Connect safety observations directly to operations with low-latency API infrastructure.
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <ShieldAlert className="mb-2 h-8 w-8 text-red-600" />
                  <CardTitle>Predictive Alerts</CardTitle>
                  <CardDescription>Identify high-risk patterns before they escalate into serious injuries.</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-600">
                    Leverage historical data to surface predictive insights and mitigate risks proactively.
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <Users className="mb-2 h-8 w-8 text-green-600" />
                  <CardTitle>Team Collaboration</CardTitle>
                  <CardDescription>Streamline communication between safety officers and on-site workers.</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-600">
                    Ensure everyone is aligned with role-based access control and targeted reporting.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white py-8">
        <div className="container mx-auto px-4 text-center text-sm text-slate-500 sm:px-8">
          <p>&copy; {new Date().getFullYear()} SIF Sentinel. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

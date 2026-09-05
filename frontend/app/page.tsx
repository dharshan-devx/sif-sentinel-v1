import { ShieldCheck, Activity, BrainCircuit } from "lucide-react";
import { Header } from "@/components/layout";
import * as motion from "framer-motion/client";

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <section className="relative overflow-hidden py-24 sm:py-32 lg:pb-40">
          <div className="absolute inset-x-0 -top-40 -z-10 transform-gpu overflow-hidden blur-3xl sm:-top-80" aria-hidden="true">
            <div className="relative left-[calc(50%-11rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-[#0f766e] to-[#0f5a5a] opacity-20 sm:left-[calc(50%-30rem)] sm:w-[72.1875rem]" />
          </div>

          <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <div className="mx-auto max-w-2xl text-center">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
              >
                <div className="mb-8 inline-flex items-center rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-sm font-medium text-primary backdrop-blur-sm">
                  <span className="flex h-2 w-2 rounded-full bg-primary mr-2 animate-pulse"></span>
                  Foundation Release
                </div>
                <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-6xl">
                  Make safety signals <span className="bg-gradient-to-r from-primary to-teal-400 bg-clip-text text-transparent">easier to see.</span>
                </h1>
                <p className="mt-6 text-lg leading-8 text-muted-foreground">
                  SIF Sentinel brings disciplined structure to operational safety information—supporting meaningful review without replacing professional judgment.
                </p>
              </motion.div>
            </div>

            <motion.div 
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
              className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none"
            >
              <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
                <div className="flex flex-col glass-card rounded-2xl p-8 hover:-translate-y-1 transition-transform duration-300">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-foreground">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                      <ShieldCheck className="h-6 w-6 text-primary" aria-hidden="true" />
                    </div>
                    Clarity before complexity
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-muted-foreground">
                    <p className="flex-auto">A clear home for consistent incident and near-miss information.</p>
                  </dd>
                </div>
                
                <div className="flex flex-col glass-card rounded-2xl p-8 hover:-translate-y-1 transition-transform duration-300">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-foreground">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                      <Activity className="h-6 w-6 text-primary" aria-hidden="true" />
                    </div>
                    Structured safety signals
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-muted-foreground">
                    <p className="flex-auto">Deterministic analysis is kept distinct from optional reviewer assistance.</p>
                  </dd>
                </div>
                
                <div className="flex flex-col glass-card rounded-2xl p-8 hover:-translate-y-1 transition-transform duration-300">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-foreground">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                      <BrainCircuit className="h-6 w-6 text-primary" aria-hidden="true" />
                    </div>
                    Deterministic by design
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-muted-foreground">
                    <p className="flex-auto">The workspace foundation is ready for authenticated, role-aware safety operations.</p>
                  </dd>
                </div>
              </dl>
            </motion.div>
          </div>
        </section>
      </main>
    </div>
  );
}

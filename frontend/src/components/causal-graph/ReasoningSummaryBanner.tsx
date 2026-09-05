import React from 'react'
import { CheckCircle2, HelpCircle, ShieldAlert, ShieldCheck, Clock, StopCircle } from 'lucide-react'
import type { CausalChain } from '../../types/analysis'

interface Props {
  summary?: string | null
  chains?: CausalChain[] | null
  sifPotential: boolean
}

export const ReasoningSummaryBanner: React.FC<Props> = ({ summary, chains, sifPotential }) => {
  if (!summary && (!chains || chains.length === 0)) return null

  const hasBarrierFailure = chains?.some((c) => c.barrier_failure) ?? sifPotential
  const hasTemporalViolation = chains?.some((c) => c.temporal_inversion) ?? false
  const hasPrevention = chains?.some((c) => c.prevention_detected) ?? false
  const isUnknown = chains?.some((c) => c.control_status === 'UNKNOWN') && !hasBarrierFailure

  return (
    <div
      role="region"
      aria-label="Causal Safety Reasoning Summary"
      className={`relative overflow-hidden rounded-xl border p-5 transition-all shadow-lg backdrop-blur-md ${
        hasBarrierFailure
          ? 'border-red-500/40 bg-gradient-to-r from-red-950/40 via-red-900/20 to-slate-900/60 text-red-100'
          : hasPrevention
          ? 'border-cyan-500/40 bg-gradient-to-r from-cyan-950/40 via-cyan-900/20 to-slate-900/60 text-cyan-100'
          : isUnknown
          ? 'border-amber-500/40 bg-gradient-to-r from-amber-950/40 via-amber-900/20 to-slate-900/60 text-amber-100'
          : 'border-emerald-500/40 bg-gradient-to-r from-emerald-950/40 via-emerald-900/20 to-slate-900/60 text-emerald-100'
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3.5 flex-1 min-w-[280px]">
          <div
            className={`p-2.5 rounded-lg flex items-center justify-center shrink-0 ${
              hasBarrierFailure
                ? 'bg-red-500/20 text-red-400 border border-red-500/30 ring-4 ring-red-500/10'
                : hasPrevention
                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 ring-4 ring-cyan-500/10'
                : isUnknown
                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30 ring-4 ring-amber-500/10'
                : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 ring-4 ring-emerald-500/10'
            }`}
          >
            {hasBarrierFailure ? (
              <ShieldAlert className="w-6 h-6 animate-pulse" />
            ) : hasPrevention ? (
              <StopCircle className="w-6 h-6" />
            ) : isUnknown ? (
              <HelpCircle className="w-6 h-6" />
            ) : (
              <ShieldCheck className="w-6 h-6" />
            )}
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-black/40 border border-white/10">
                {hasBarrierFailure
                  ? 'CRITICAL BARRIER FAILURE'
                  : hasPrevention
                  ? 'PREVENTION INTERVENTION'
                  : isUnknown
                  ? 'BARRIER STATUS UNCERTAIN'
                  : 'SAFETY BARRIERS INTACT'}
              </span>

              {hasTemporalViolation && (
                <span className="text-xs font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1">
                  <Clock className="w-3 h-3" /> Sequence Violation
                </span>
              )}

              {hasPrevention && (
                <span className="text-xs font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Stop Work Intervention
                </span>
              )}
            </div>

            <h3 className="text-base font-medium leading-snug tracking-tight text-white/95">
              {summary ||
                (hasBarrierFailure
                  ? 'High-energy hazard detected with compromised or unverified safety barrier.'
                  : 'Hazard verified with compliant barrier controls.')}
            </h3>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <div className="text-right">
            <div className="text-xs text-slate-400 font-mono">Deduction Method</div>
            <div className="text-xs font-semibold text-slate-200">
              Deterministic Causal Graph
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

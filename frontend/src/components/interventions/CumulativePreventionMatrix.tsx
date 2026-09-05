import React from 'react'
import { ShieldCheck, Layers, TrendingDown, AlertTriangle } from 'lucide-react'
import type { CumulativePreventionPlan } from '../../types/analysis'


interface CumulativePreventionMatrixProps {
  plan: CumulativePreventionPlan
  onSimulateStep?: (barrierName: string) => void
}

export const CumulativePreventionMatrix: React.FC<CumulativePreventionMatrixProps> = ({
  plan,
  onSimulateStep,
}) => {
  return (
    <div className="bg-slate-900/90 border border-slate-800/90 rounded-2xl p-5 space-y-6 shadow-xl backdrop-blur-md">
      {/* Header Section */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-600 shadow-lg shadow-emerald-900/30 flex items-center justify-center">
            <Layers className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              Multi-Barrier Cumulative Prevention Matrix
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Defense-in-Depth
              </span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Sequential barrier restoration trajectory computed via canonical deterministic safety models.
            </p>
          </div>
        </div>

        {/* High-level Risk Delta Summary Badge */}
        <div className="flex items-center gap-3 bg-slate-950/80 px-4 py-2 rounded-xl border border-slate-800">
          <div className="text-right">
            <div className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">
              Total Risk Reduction
            </div>
            <div className="text-sm font-bold text-emerald-400 font-mono">
              {plan.baseline_risk} → {plan.target_risk} pts ({plan.total_risk_delta} ΔR)
            </div>
          </div>
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <TrendingDown className="w-4 h-4" />
          </div>
        </div>
      </div>

      {/* Trajectory Stepper */}
      <div className="space-y-3">
        <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-cyan-400" />
          Sequential Barrier Restoration Trajectory
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {plan.trajectory.map((step) => {
            const isTargetReached = step.simulated_risk_score <= 25

            return (
              <div
                key={step.step_number}
                className="relative bg-slate-950/70 border border-slate-800/80 hover:border-emerald-500/40 rounded-xl p-4 space-y-3 transition-all group"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center text-[10px] font-mono font-bold border border-slate-700">
                      {step.step_number}
                    </span>
                    <span className="text-xs font-bold text-slate-200">
                      {step.barrier_name}
                    </span>
                  </div>
                  <span
                    className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full ${
                      step.step_risk_delta < 0
                        ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {step.step_risk_delta} pts
                  </span>
                </div>

                <div className="text-xs text-slate-400 line-clamp-2">
                  {step.action_title}
                </div>

                <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-xs">
                  <div>
                    <span className="text-[10px] text-slate-500 block">Post-Step Risk:</span>
                    <span
                      className={`font-mono font-bold text-xs ${
                        isTargetReached ? 'text-emerald-400' : 'text-amber-400'
                      }`}
                    >
                      {step.simulated_risk_score} / 100
                    </span>
                  </div>

                  {onSimulateStep && (
                    <button
                      onClick={() => onSimulateStep(step.barrier_name)}
                      className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 text-[10px] font-semibold transition-colors border border-slate-700"
                    >
                      Inspect What-If
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Assumptions & Governance Footer */}
      <div className="bg-slate-950/50 rounded-xl p-3.5 border border-slate-800/60 space-y-2 text-xs">
        <div className="font-semibold text-slate-300 flex items-center gap-1.5 text-[11px] uppercase tracking-wider">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          Model Assumptions & Governance Criteria
        </div>
        <ul className="list-disc list-inside space-y-1 text-slate-400 text-[11px]">
          {plan.assumptions.map((assump, idx) => (
            <li key={idx} className="leading-relaxed">
              {assump}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

import React from 'react'
import type { CausalChain } from '../../types/analysis'
import {
  Activity,
  Flame,
  Shield,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  ArrowRight,
  ShieldAlert,
  ShieldCheck,
} from 'lucide-react'

interface Props {
  chains: CausalChain[]
  selectedChainIdx: number
  onSelectChain: (idx: number) => void
  onSelectStep?: (stepName: string) => void
}

export const CausalChainStepper: React.FC<Props> = ({
  chains,
  selectedChainIdx,
  onSelectChain,
  onSelectStep,
}) => {
  if (!chains || chains.length === 0) {
    return (
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 text-center">
        No causal chains evaluated for this report.
      </div>
    )
  }

  const activeChain = chains[selectedChainIdx] || chains[0]

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'VERIFIED':
      case 'PERFORMED':
        return {
          bg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
          icon: <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />,
        }
      case 'NOT_VERIFIED':
      case 'NOT_PERFORMED':
      case 'FAILED':
      case 'BYPASSED':
      case 'MISSING':
      case 'EXPIRED':
        return {
          bg: 'bg-red-500/20 text-red-300 border-red-500/30',
          icon: <ShieldAlert className="w-3.5 h-3.5 text-red-400" />,
        }
      default:
        return {
          bg: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
          icon: <HelpCircle className="w-3.5 h-3.5 text-amber-400" />,
        }
    }
  }

  const statusBadge = getStatusBadge(activeChain.control_status)

  const steps = [
    {
      id: 'activity',
      name: 'Activity',
      val: activeChain.activity,
      icon: <Activity className="w-4 h-4 text-violet-400" />,
      tag: 'Operation',
    },
    {
      id: 'hazard',
      name: 'Hazard',
      val: activeChain.hazard,
      icon: <Flame className="w-4 h-4 text-amber-400" />,
      tag: 'Hazardous Energy',
    },
    {
      id: 'control',
      name: 'Required Barrier',
      val: activeChain.control,
      icon: <Shield className="w-4 h-4 text-blue-400" />,
      tag: 'Critical Control',
    },
    {
      id: 'status',
      name: 'Barrier Status',
      val: activeChain.control_status.replace(/_/g, ' '),
      icon: statusBadge.icon,
      badge: statusBadge.bg,
      tag: 'Evaluation',
    },
    {
      id: 'exposure',
      name: 'Causal Exposure',
      val: activeChain.exposure,
      icon: activeChain.barrier_failure ? (
        <AlertTriangle className="w-4 h-4 text-red-400" />
      ) : (
        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
      ),
      tag: 'Exposure Outcome',
    },
  ]

  return (
    <div className="space-y-3">
      {chains.length > 1 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider shrink-0">
            Causal Chains:
          </span>
          {chains.map((c, i) => (
            <button
              key={i}
              onClick={() => onSelectChain(i)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-all shrink-0 flex items-center gap-1.5 border ${
                selectedChainIdx === i
                  ? 'bg-cyan-500/20 text-cyan-200 border-cyan-500/50 shadow-sm'
                  : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              <span>Chain #{i + 1}</span>
              <span className="text-[10px] text-slate-500 font-mono">({c.control_status})</span>
            </button>
          ))}
        </div>
      )}

      {/* Stepper Chain Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-2.5">
        {steps.map((step, idx) => (
          <div
            key={step.id}
            onClick={() => onSelectStep?.(step.id)}
            role="button"
            tabIndex={0}
            className="group relative p-3 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 hover:bg-slate-850 transition-all cursor-pointer shadow-sm flex flex-col justify-between min-h-[92px]"
          >
            <div>
              <div className="flex items-center justify-between gap-1 mb-1.5">
                <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
                  {step.icon}
                  <span>{step.name}</span>
                </div>
                <span className="text-[9px] font-mono uppercase px-1.5 py-0.2 rounded bg-slate-950 text-slate-500 border border-slate-800">
                  {step.tag}
                </span>
              </div>
              <div className="text-xs font-semibold text-white group-hover:text-cyan-300 transition-colors line-clamp-2">
                {step.val}
              </div>
            </div>

            {idx < steps.length - 1 && (
              <div className="hidden md:block absolute -right-2 top-1/2 -translate-y-1/2 z-10 p-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-400 pointer-events-none">
                <ArrowRight className="w-3 h-3" />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

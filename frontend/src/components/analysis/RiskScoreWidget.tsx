import React from 'react'
import type { RiskDetail, SIFLevel } from '../../types/analysis'
import { ShieldCheck, ShieldAlert, BookOpen } from 'lucide-react'

interface Props {
  risk?: RiskDetail | null
  sifPotential: boolean
  sifLevel: SIFLevel
  lsr?: string | null
  probability: number
}

export const RiskScoreWidget: React.FC<Props> = ({
  risk,
  sifPotential,
  sifLevel,
  lsr,
  probability,
}) => {
  const score = risk?.score ?? (sifPotential ? 85 : 15)
  const priority = risk?.priority ?? (sifPotential ? 'P1_CRITICAL' : 'P4_LOW')

  const getPriorityBadge = (p: string) => {
    switch (p) {
      case 'P1_CRITICAL':
        return 'bg-red-500/20 text-red-300 border-red-500/40'
      case 'P2_HIGH':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40'
      case 'P3_MEDIUM':
        return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40'
      default:
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
    }
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      {/* SIF Potential Card */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span className="font-semibold uppercase tracking-wider">SIF Classification</span>
          <span className="font-mono text-cyan-400">{(probability * 100).toFixed(1)}% Prob</span>
        </div>
        <div className="my-2">
          <div className="text-xl font-bold text-white flex items-center gap-2">
            {sifPotential ? (
              <>
                <ShieldAlert className="w-5 h-5 text-red-400" />
                <span className="text-red-400">POTENTIAL SIF</span>
              </>
            ) : (
              <>
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <span className="text-emerald-400">NON-SIF</span>
              </>
            )}
          </div>
          <div className="text-xs text-slate-400 mt-1">Level: {sifLevel}</div>
        </div>
        <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              sifPotential ? 'bg-red-500' : 'bg-emerald-500'
            }`}
            style={{ width: `${Math.max(probability * 100, 5)}%` }}
          />
        </div>
      </div>

      {/* Risk Priority & Score */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span className="font-semibold uppercase tracking-wider">Composite Risk</span>
          <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${getPriorityBadge(priority)}`}>
            {priority}
          </span>
        </div>
        <div className="my-2 flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-white font-mono">{score}</span>
          <span className="text-xs text-slate-400">/ 100 Score</span>
        </div>
        <div className="text-xs text-slate-400 line-clamp-1">
          {risk?.components?.[0]?.reason || 'Calculated from energy & barrier state'}
        </div>
      </div>

      {/* Life-Saving Rule */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span className="font-semibold uppercase tracking-wider">Life-Saving Rule</span>
          <BookOpen className="w-4 h-4 text-cyan-400" />
        </div>
        <div className="my-2">
          <div className="text-sm font-bold text-cyan-200 line-clamp-2">
            {lsr || 'General Safe Work System'}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Standard IOGP / Energy Institute LSR
          </div>
        </div>
        <div className="text-[10px] text-slate-500 font-mono">
          Governing Barrier Protocol
        </div>
      </div>
    </div>
  )
}

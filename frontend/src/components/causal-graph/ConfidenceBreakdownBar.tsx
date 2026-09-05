import React from 'react'
import type { ConfidenceBreakdown } from '../../types/analysis'

interface Props {
  breakdown?: ConfidenceBreakdown | null
  overallConfidence?: number
}

export const ConfidenceBreakdownBar: React.FC<Props> = ({ breakdown, overallConfidence = 0.9 }) => {
  const model = breakdown?.model_confidence ?? 0.9
  const extraction = breakdown?.extraction_confidence ?? 0.92
  const relationship = breakdown?.relationship_confidence ?? 0.9
  const evidence = breakdown?.evidence_confidence ?? 0.94
  const overall = breakdown?.overall_reasoning_confidence ?? overallConfidence

  const getTier = (val: number) => {
    if (val >= 0.85) return { label: 'High Confidence', color: 'text-emerald-400', bar: 'bg-emerald-500' }
    if (val >= 0.65) return { label: 'Moderate', color: 'text-amber-400', bar: 'bg-amber-500' }
    return { label: 'Requires Review', color: 'text-rose-400', bar: 'bg-rose-500' }
  }

  const overallTier = getTier(overall)

  return (
    <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-4 shadow-sm backdrop-blur-sm">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Multi-Dimensional Confidence
          </span>
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 ${overallTier.color}`}>
            {overallTier.label}
          </span>
        </div>
        <div className="text-sm font-mono font-bold text-white">
          {(overall * 100).toFixed(0)}% <span className="text-xs font-normal text-slate-400">Overall</span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div>
          <div className="flex justify-between text-slate-400 mb-1">
            <span>Evidence</span>
            <span className="font-mono text-slate-200">{(evidence * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div className="bg-cyan-500 h-full rounded-full transition-all duration-500" style={{ width: `${evidence * 100}%` }} />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-slate-400 mb-1">
            <span>Extraction</span>
            <span className="font-mono text-slate-200">{(extraction * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div className="bg-violet-500 h-full rounded-full transition-all duration-500" style={{ width: `${extraction * 100}%` }} />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-slate-400 mb-1">
            <span>Relationship</span>
            <span className="font-mono text-slate-200">{(relationship * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div className="bg-amber-500 h-full rounded-full transition-all duration-500" style={{ width: `${relationship * 100}%` }} />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-slate-400 mb-1">
            <span>Transformer</span>
            <span className="font-mono text-slate-200">{(model * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div className="bg-blue-500 h-full rounded-full transition-all duration-500" style={{ width: `${model * 100}%` }} />
          </div>
        </div>
      </div>
    </div>
  )
}

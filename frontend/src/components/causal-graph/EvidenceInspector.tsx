import React from 'react'
import type { EvidenceGrounding } from '../../types/analysis'
import { Quote, Tag } from 'lucide-react'

interface Props {
  evidenceList: EvidenceGrounding[]
  reportText?: string
}

export const EvidenceInspector: React.FC<Props> = ({ evidenceList }) => {
  if (!evidenceList || evidenceList.length === 0) {
    return (
      <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-800 text-xs text-slate-400 text-center">
        No direct evidence span grounded for this element.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-slate-400">
        <span className="flex items-center gap-1.5">
          <Quote className="w-3.5 h-3.5 text-cyan-400" /> Grounded Source Evidence
        </span>
        <span className="font-mono text-cyan-400">{evidenceList.length} Claim{evidenceList.length > 1 ? 's' : ''}</span>
      </div>

      <div className="space-y-2.5">
        {evidenceList.map((item, idx) => (
          <div
            key={idx}
            className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition-all text-xs space-y-2"
          >
            <div className="flex items-start justify-between gap-2">
              <span className="font-semibold text-slate-200 leading-snug">{item.claim}</span>
              <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] font-mono text-cyan-300 shrink-0">
                {(item.confidence * 100).toFixed(0)}% Conf
              </span>
            </div>

            <div className="p-2 rounded bg-slate-950/80 border-l-2 border-cyan-500 font-mono text-slate-300 text-[11px] leading-relaxed">
              "{item.evidence}"
            </div>

            <div className="flex items-center justify-between text-[10px] text-slate-400">
              <span className="flex items-center gap-1">
                <Tag className="w-3 h-3 text-slate-400" /> {item.evidence_type}
              </span>
              {item.source_span && (
                <span className="font-mono">
                  Offset: [{item.source_span[0]}:{item.source_span[1]}]
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

import React, { useState } from 'react'
import { Sparkles, Send } from 'lucide-react'

interface Props {
  onAnalyze: (text: string) => void
  isLoading: boolean
}

export const PRESET_SCENARIOS = [
  {
    title: 'Confined Space - Gas Testing Omission',
    tag: 'Barrier Failure',
    text: 'Worker entered nitrogen purge vessel without atmospheric gas testing or permit to work authorization.',
  },
  {
    title: 'Working at Height - Compliant Tie-Off',
    tag: 'Safe Execution',
    text: 'Rigger climbed monkey board on drilling rig with 100% tie-off safety harness and verified dual lanyards.',
  },
  {
    title: 'Hazardous Energy - Line Removal Without LOTO',
    tag: 'Energy Failure',
    text: 'Technician removed hydraulic valve while line remained pressurized, without conducting lock out tag out or zero energy check.',
  },
  {
    title: 'Preventive Stop-Work Intervention',
    tag: 'Intervention',
    text: 'Safety officer intervened and stopped contractor from working at height without fall protection.',
  },
  {
    title: 'Temporal Violation - Sequence Inversion',
    tag: 'Sequence Violation',
    text: 'Worker entered reactor tank before atmospheric gas testing was completed by technician.',
  },
]

export const IncidentInput: React.FC<Props> = ({ onAnalyze, isLoading }) => {
  const [text, setText] = useState(PRESET_SCENARIOS[0].text)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim() || isLoading) return
    onAnalyze(text.trim())
  }

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-lg backdrop-blur-md space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" /> Incident Narrative Analysis
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Submit an HSE safety report to evaluate causal barrier chains and SIF potential
          </p>
        </div>
      </div>

      {/* Quick Scenario Selector */}
      <div>
        <div className="text-[11px] font-mono text-slate-400 uppercase mb-2">
          Demo Safety Scenarios:
        </div>
        <div className="flex flex-wrap gap-2">
          {PRESET_SCENARIOS.map((scenario, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setText(scenario.text)
                onAnalyze(scenario.text)
              }}
              className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 hover:border-cyan-500/50 hover:bg-slate-850 text-xs text-left transition-all group flex items-center gap-2"
            >
              <span className="font-medium text-slate-300 group-hover:text-cyan-300">
                {scenario.title}
              </span>
              <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-slate-900 text-slate-400 border border-slate-700">
                {scenario.tag}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Live Narrative Input Area */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="relative">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={3}
            placeholder="Type or paste unsafe act, unsafe condition, or near-miss safety narrative..."
            className="w-full rounded-xl bg-slate-950 border border-slate-800 p-3.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all font-sans leading-relaxed resize-y"
          />
        </div>

        <div className="flex items-center justify-between">
          <span className="text-[11px] text-slate-500 font-mono">
            {text.length} characters • Causal Model v5B
          </span>

          <button
            type="submit"
            disabled={isLoading || !text.trim()}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-bold transition-all shadow-md shadow-cyan-900/30 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Evaluating Causal Graph...</span>
              </>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                <span>Run Causal Safety Analysis</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}

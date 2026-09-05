import React from 'react'
import type { GraphNode, CausalChain, CounterfactualScenario, SafetyReasoningGraph } from '../../types/analysis'
import { EvidenceInspector } from './EvidenceInspector'
import { CounterfactualSimulationPanel } from './CounterfactualSimulationPanel'
import { X, Activity, Flame, Shield, AlertOctagon, CheckCircle2, FileText, Info } from 'lucide-react'

interface Props {
  node: GraphNode | null
  activeChain: CausalChain | null
  safetyGraph?: SafetyReasoningGraph | null
  riskScore?: number | null
  reportText?: string
  activeScenario: CounterfactualScenario | null
  onScenarioUpdate: (scenario: CounterfactualScenario | null) => void
  onClose: () => void
}

export const NodeDetailsPanel: React.FC<Props> = ({
  node,
  activeChain,
  safetyGraph,
  riskScore,
  reportText,
  activeScenario,
  onScenarioUpdate,
  onClose,
}) => {
  if (!node && !activeChain) return null

  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'ACTIVITY':
        return <Activity className="w-5 h-5 text-violet-400" />
      case 'HAZARD':
        return <Flame className="w-5 h-5 text-amber-400" />
      case 'CONTROL':
        return <Shield className="w-5 h-5 text-blue-400" />
      case 'STATUS':
        return <Info className="w-5 h-5 text-emerald-400" />
      case 'EXPOSURE':
      case 'PRECURSOR':
        return <AlertOctagon className="w-5 h-5 text-red-400" />
      default:
        return <FileText className="w-5 h-5 text-slate-400" />
    }
  }

  const title = node?.label || activeChain?.control || 'Causal Element Details'
  const type = node?.type || 'CAUSAL_CHAIN'
  const confidence = node?.confidence ?? activeChain?.confidence ?? 0.92

  // Gather relevant evidence items
  const evidenceList = activeChain?.evidence || []

  return (
    <aside
      aria-label="Causal Node Details Inspector"
      className="w-full lg:w-88 shrink-0 bg-slate-900/95 border border-slate-800 rounded-xl p-4 shadow-xl backdrop-blur-md flex flex-col gap-4 max-h-[680px] overflow-y-auto"
    >
      <div className="flex items-start justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-slate-800 border border-slate-700">
            {getNodeIcon(type)}
          </div>
          <div>
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
              {type}
            </span>
            <h4 className="text-sm font-bold text-white leading-tight">{title}</h4>
          </div>
        </div>
        <button
          onClick={onClose}
          aria-label="Close details panel"
          className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-3 text-xs">
        <div className="flex justify-between items-center p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80">
          <span className="text-slate-400">Deduction Confidence</span>
          <span className="font-mono font-bold text-cyan-400">
            {(confidence * 100).toFixed(0)}%
          </span>
        </div>

        {node?.status && (
          <div className="flex justify-between items-center p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80">
            <span className="text-slate-400">Control State</span>
            <span className="font-mono font-semibold text-slate-200">
              {node.status}
            </span>
          </div>
        )}

        {activeChain && (
          <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800/80 space-y-1.5">
            <div className="text-slate-400 font-semibold">Causal Outcome</div>
            <div className="text-slate-200">
              {activeChain.barrier_failure ? (
                <span className="text-red-400 font-bold flex items-center gap-1">
                  <AlertOctagon className="w-3.5 h-3.5" /> Barrier Compromised → SIF Precursor
                </span>
              ) : (
                <span className="text-emerald-400 font-bold flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Barrier Verified → Safe Execution
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Phase 5D Counterfactual Simulation Panel */}
      <CounterfactualSimulationPanel
        node={node}
        activeChain={activeChain}
        safetyGraph={safetyGraph}
        riskScore={riskScore}
        activeScenario={activeScenario}
        onScenarioUpdate={onScenarioUpdate}
      />

      <EvidenceInspector evidenceList={evidenceList} reportText={reportText} />
    </aside>
  )
}

import React, { useState } from 'react'
import type {
  GraphNode,
  CausalChain,
  CounterfactualScenario,
  SafetyReasoningGraph,
} from '../../types/analysis'
import { simulateCounterfactual } from '../../services/api'
import {
  Sparkles,
  RotateCcw,
  ArrowRight,
  TrendingDown,
  CheckCircle2,
  AlertCircle,
  Play,
} from 'lucide-react'

interface Props {
  node?: GraphNode | null
  activeChain?: CausalChain | null
  safetyGraph?: SafetyReasoningGraph | null
  riskScore?: number | null
  activeScenario: CounterfactualScenario | null
  onScenarioUpdate: (scenario: CounterfactualScenario | null) => void
}

export const CounterfactualSimulationPanel: React.FC<Props> = ({
  node,
  activeChain,
  safetyGraph,
  riskScore,
  activeScenario,
  onScenarioUpdate,
}) => {
  const [simStatus, setSimStatus] = useState<'VERIFIED' | 'PERFORMED'>('VERIFIED')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const targetControl =
    node?.type === 'CONTROL'
      ? node.label
      : activeChain?.control || 'Atmospheric Testing / Gas Monitoring'

  const handleRunSimulation = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const scenario = await simulateCounterfactual({
        target_control: targetControl,
        target_node_id: node?.id,
        simulated_status: simStatus,
        safety_graph: safetyGraph,
        risk_score: riskScore ?? 85,
      })
      onScenarioUpdate(scenario)
    } catch (err: any) {
      console.error('Counterfactual simulation failed:', err)
      setError(err.message || 'Simulation failed.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleReset = () => {
    onScenarioUpdate(null)
    setError(null)
  }

  return (
    <div
      role="region"
      aria-label="Counterfactual Safety Simulation Engine"
      className="p-4 rounded-xl bg-slate-950/90 border border-slate-800 shadow-md space-y-3.5 backdrop-blur-sm"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-cyan-400">
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <span>What-If Safety Simulation</span>
        </div>
        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
          Phase 5D Engine
        </span>
      </div>

      <p className="text-[11px] text-slate-400 leading-snug">
        Simulate the risk and barrier outcome if <span className="font-semibold text-slate-200">'{targetControl}'</span> had been verified.
      </p>

      {/* Simulator Controls */}
      <div className="flex items-center gap-2">
        <div className="flex-1">
          <label className="text-[10px] text-slate-400 font-mono block mb-1">
            Simulate Barrier Status:
          </label>
          <select
            value={simStatus}
            onChange={(e) => setSimStatus(e.target.value as 'VERIFIED' | 'PERFORMED')}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-sans"
          >
            <option value="VERIFIED">VERIFIED (100% Verified Compliant)</option>
            <option value="PERFORMED">PERFORMED (Successfully Executed)</option>
          </select>
        </div>

        <button
          onClick={handleRunSimulation}
          disabled={isLoading}
          className="self-end px-3 py-1.5 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-bold transition-all shadow-md shadow-cyan-900/30 flex items-center gap-1.5 shrink-0 disabled:opacity-50"
        >
          {isLoading ? (
            <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <Play className="w-3.5 h-3.5 fill-current" />
          )}
          <span>Simulate</span>
        </button>
      </div>

      {error && (
        <div className="p-2.5 rounded-lg bg-red-950/40 border border-red-500/30 text-[11px] text-red-300 flex items-center gap-1.5">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Counterfactual Results Card */}
      {activeScenario && (
        <div className="space-y-3 pt-2 border-t border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-400 font-bold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Simulation Active
            </span>
            <button
              onClick={handleReset}
              className="text-[10px] text-slate-400 hover:text-white flex items-center gap-1 transition-colors"
            >
              <RotateCcw className="w-3 h-3" /> Reset Baseline
            </button>
          </div>

          {/* Quantitative Risk Delta Banner */}
          <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-500/40 flex items-center justify-between">
            <div>
              <div className="text-[10px] text-emerald-300 font-mono">Simulated Risk Delta</div>
              <div className="text-lg font-bold text-white flex items-baseline gap-1.5">
                <span>{activeScenario.original_risk_score}</span>
                <ArrowRight className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400 font-extrabold">{activeScenario.simulated_risk_score}</span>
                <span className="text-xs text-slate-400">/ 100</span>
              </div>
            </div>
            <div className="px-2.5 py-1 rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs font-mono font-bold flex items-center gap-1">
              <TrendingDown className="w-3.5 h-3.5" />
              {activeScenario.risk_delta} Pts
            </div>
          </div>

          {/* Causal Delta Comparison Grid */}
          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div className="p-2 rounded bg-slate-900 border border-slate-800 space-y-1">
              <div className="text-[9px] uppercase font-mono text-slate-500">Barrier State</div>
              <div className="text-slate-300">
                <span className="line-through text-red-400">{activeScenario.original_status}</span>
                <span className="text-emerald-400 font-bold ml-1.5">→ {activeScenario.simulated_status}</span>
              </div>
            </div>

            <div className="p-2 rounded bg-slate-900 border border-slate-800 space-y-1">
              <div className="text-[9px] uppercase font-mono text-slate-500">Barrier Outcome</div>
              <div className="text-slate-300">
                <span className="line-through text-red-400">FAILED</span>
                <span className="text-emerald-400 font-bold ml-1.5">→ RESTORED</span>
              </div>
            </div>

            <div className="p-2 rounded bg-slate-900 border border-slate-800 space-y-1">
              <div className="text-[9px] uppercase font-mono text-slate-500">Causal Exposure</div>
              <div className="text-slate-300">
                <span className="line-through text-red-400">EXPOSURE</span>
                <span className="text-emerald-400 font-bold ml-1.5">→ MITIGATED</span>
              </div>
            </div>

            <div className="p-2 rounded bg-slate-900 border border-slate-800 space-y-1">
              <div className="text-[9px] uppercase font-mono text-slate-500">SIF Precursor</div>
              <div className="text-slate-300">
                <span className="line-through text-red-400">{activeScenario.original_sif_classification}</span>
                <span className="text-emerald-400 font-bold ml-1.5">→ {activeScenario.simulated_sif_classification}</span>
              </div>
            </div>
          </div>

          {/* Grounded Interpretation */}
          <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800 text-[11px] text-slate-300 space-y-1">
            <div className="text-[10px] font-mono text-slate-400 uppercase font-semibold">
              Deterministic Interpretation
            </div>
            <p className="leading-relaxed">{activeScenario.interpretation}</p>
          </div>

          {/* Audit Assumptions Note */}
          <div className="text-[9px] text-slate-500 font-mono space-y-0.5">
            <div>• {activeScenario.assumptions[0]}</div>
            <div>• {activeScenario.assumptions[4]}</div>
          </div>
        </div>
      )}
    </div>
  )
}

import React, { useState } from 'react'
import type {
  SafetyReasoningGraph,
  CausalChain,
  CounterfactualScenario,
} from '../../types/analysis'
import { ReasoningSummaryBanner } from './ReasoningSummaryBanner'
import { ConfidenceBreakdownBar } from './ConfidenceBreakdownBar'
import { CausalChainStepper } from './CausalChainStepper'
import { GraphCanvas } from './GraphCanvas'
import { NodeDetailsPanel } from './NodeDetailsPanel'
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Layers,
  Sparkles,
} from 'lucide-react'

interface Props {
  safetyGraph?: SafetyReasoningGraph | null
  causalChains?: CausalChain[] | null
  reasoningSummary?: string | null
  sifPotential: boolean
  overallConfidence?: number
  riskScore?: number | null
  reportText?: string
  onScenarioChange?: (scenario: CounterfactualScenario | null) => void
}

export const CausalSafetyGraph: React.FC<Props> = ({
  safetyGraph,
  causalChains,
  reasoningSummary,
  sifPotential,
  overallConfidence = 0.92,
  riskScore = 85,
  reportText,
  onScenarioChange,
}) => {

  const [selectedChainIdx, setSelectedChainIdx] = useState(0)
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [filterMode, setFilterMode] = useState<'ALL' | 'FAILURES' | 'VERIFIED'>('ALL')
  const [viewMode, setViewMode] = useState<'OBSERVED' | 'SIMULATED' | 'COMPARE'>('OBSERVED')
  const [activeScenario, setActiveScenario] = useState<CounterfactualScenario | null>(null)
  const [zoomLevel, setZoomLevel] = useState(1.0)
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 })

  const chains = causalChains || safetyGraph?.causal_chains || []
  const nodes = safetyGraph?.nodes || []
  const edges = safetyGraph?.edges || []
  const activeChain = chains[selectedChainIdx] || null

  // Find currently selected node
  const selectedNode = selectedNodeId
    ? nodes.find((n) => n.id === selectedNodeId) || null
    : null

  const handleZoomIn = () => setZoomLevel((z) => Math.min(z + 0.15, 1.8))
  const handleZoomOut = () => setZoomLevel((z) => Math.max(z - 0.15, 0.6))
  const handleResetView = () => {
    setZoomLevel(1.0)
    setPanOffset({ x: 0, y: 0 })
  }

  // Graceful empty / fallback state
  if (!safetyGraph && (!chains || chains.length === 0)) {
    return (
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 text-center space-y-2">
        <div className="text-slate-400 text-sm font-medium">
          Causal safety reasoning is not available for this analysis report.
        </div>
        <div className="text-xs text-slate-500">
          Standard classification and evidence signals remain active.
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* 1. Reasoning Summary Top Banner */}
      <ReasoningSummaryBanner
        summary={reasoningSummary || safetyGraph?.summary}
        chains={chains}
        sifPotential={sifPotential}
      />

      {/* Counterfactual Active Alert Banner */}
      {activeScenario && (
        <div className="p-3.5 rounded-xl bg-gradient-to-r from-emerald-950/60 via-slate-900 to-slate-950 border border-emerald-500/50 flex flex-wrap items-center justify-between gap-3 shadow-md">
          <div className="flex items-center gap-2.5">
            <span className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
              <Sparkles className="w-4 h-4" />
            </span>
            <div>
              <div className="text-xs font-bold text-white flex items-center gap-1.5">
                <span>Simulation Active:</span>
                <span className="text-emerald-300 font-mono">
                  {activeScenario.target_control} ({activeScenario.simulated_status})
                </span>
              </div>
              <div className="text-[11px] text-slate-300">
                Risk reduced from {activeScenario.original_risk_score} to {activeScenario.simulated_risk_score} (
                <span className="text-emerald-400 font-mono font-bold">{activeScenario.risk_delta} pts</span>).
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-[10px] uppercase font-mono text-slate-400">View:</span>
            <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-[11px]">
              <button
                onClick={() => setViewMode('OBSERVED')}
                className={`px-2 py-0.5 rounded font-medium transition-all ${
                  viewMode === 'OBSERVED'
                    ? 'bg-slate-700 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Observed
              </button>
              <button
                onClick={() => setViewMode('SIMULATED')}
                className={`px-2 py-0.5 rounded font-medium transition-all ${
                  viewMode === 'SIMULATED'
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Simulated
              </button>
              <button
                onClick={() => setViewMode('COMPARE')}
                className={`px-2 py-0.5 rounded font-medium transition-all ${
                  viewMode === 'COMPARE'
                    ? 'bg-cyan-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Compare
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 2. Stepper Causal Chain Overview */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider">
          <span className="flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-cyan-400" /> Causal Reasoning Timeline
          </span>
          <span className="font-mono text-cyan-400">
            {chains.length} Active Path{chains.length > 1 ? 's' : ''}
          </span>
        </div>
        <CausalChainStepper
          chains={chains}
          selectedChainIdx={selectedChainIdx}
          onSelectChain={(idx) => {
            setSelectedChainIdx(idx)
            setSelectedNodeId(null)
          }}
          onSelectStep={(stepId) => {
            const matchingNode = nodes.find(
              (n) => n.type.toLowerCase() === stepId.toLowerCase()
            )
            if (matchingNode) setSelectedNodeId(matchingNode.id)
          }}
        />
      </div>

      {/* 3. Multi-Dimensional Confidence Meter */}
      <ConfidenceBreakdownBar
        breakdown={activeChain?.confidence_breakdown}
        overallConfidence={overallConfidence}
      />

      {/* 4. Interactive Graph Toolbar + Canvas & Inspector */}
      <div className="space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Filter:
            </span>
            <button
              onClick={() => setFilterMode('ALL')}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                filterMode === 'ALL'
                  ? 'bg-slate-700 text-white'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200'
              }`}
            >
              All Nodes
            </button>
            <button
              onClick={() => setFilterMode('FAILURES')}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                filterMode === 'FAILURES'
                  ? 'bg-red-500/20 text-red-300 border border-red-500/40'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200'
              }`}
            >
              Barrier Failures
            </button>
            <button
              onClick={() => setFilterMode('VERIFIED')}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                filterMode === 'VERIFIED'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200'
              }`}
            >
              Verified Controls
            </button>
          </div>

          <div className="flex items-center gap-1 bg-slate-900/90 border border-slate-800 rounded-lg p-1">
            <button
              onClick={handleZoomIn}
              aria-label="Zoom in"
              className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleZoomOut}
              aria-label="Zoom out"
              className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleResetView}
              aria-label="Reset view"
              className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1 min-w-0">
            <GraphCanvas
              nodes={nodes}
              edges={edges}
              selectedNodeId={selectedNodeId}
              activeChainIdx={selectedChainIdx}
              filterMode={filterMode}
              zoomLevel={zoomLevel}
              panOffset={panOffset}
              activeScenario={activeScenario}
              viewMode={viewMode}
              onSelectNode={(nodeId) => setSelectedNodeId(nodeId)}
              onPanChange={(offset) => setPanOffset(offset)}
            />
          </div>

          {(selectedNode || activeChain) && (
            <NodeDetailsPanel
              node={selectedNode}
              activeChain={activeChain}
              safetyGraph={safetyGraph}
              riskScore={riskScore}
              reportText={reportText}
              activeScenario={activeScenario}
              onScenarioUpdate={(sc) => {
                setActiveScenario(sc)
                onScenarioChange?.(sc)
                if (sc) setViewMode('COMPARE')
                else setViewMode('OBSERVED')
              }}
              onClose={() => setSelectedNodeId(null)}
            />
          )}
        </div>
      </div>
    </div>
  )
}


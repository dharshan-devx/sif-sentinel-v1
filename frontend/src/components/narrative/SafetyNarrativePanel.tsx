import React, { useState, useEffect } from 'react'
import type {
  NarrativeMode,
  NarrativeResponse,
  SafetyReasoningGraph,
  CausalChain,
  CounterfactualScenario,
} from '../../types/analysis'
import { generateNarrative } from '../../services/api'
import {
  Sparkles,
  ShieldAlert,
  FileSearch,
  HardHat,
  GitFork,
  CheckCircle2,
  AlertTriangle,
  Layers,
  ArrowRight,
  HelpCircle,
  Clock,
  Cpu,
  RefreshCw,
} from 'lucide-react'

interface Props {
  incidentText: string
  safetyGraph?: SafetyReasoningGraph | null
  causalChains?: CausalChain[] | null
  riskScore?: number | null
  riskPriority?: string | null
  sifPotential?: boolean | null
  sifLevel?: string | null
  lifeSavingRule?: string | null
  evidenceSpan?: string | null
  evidenceTerms?: string[]
  counterfactualScenario?: CounterfactualScenario | null
  confidence?: number | null
}

export const SafetyNarrativePanel: React.FC<Props> = ({
  incidentText,
  safetyGraph,
  causalChains,
  riskScore = 85,
  riskPriority = 'CRITICAL',
  sifPotential = true,
  sifLevel = 'PSIF',
  lifeSavingRule,
  evidenceSpan,
  evidenceTerms = [],
  counterfactualScenario,
  confidence = 0.94,
}) => {
  const [activeMode, setActiveMode] = useState<NarrativeMode>('EXECUTIVE')
  const [narrative, setNarrative] = useState<NarrativeResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [showGrounding, setShowGrounding] = useState(false)

  // Automatically switch to COUNTERFACTUAL tab when a simulation becomes active
  useEffect(() => {
    if (counterfactualScenario) {
      setActiveMode('COUNTERFACTUAL')
    }
  }, [counterfactualScenario])

  // Fetch narrative whenever mode, text, or counterfactual changes
  useEffect(() => {
    if (!incidentText) return

    const loadNarrative = async () => {
      setIsLoading(true)
      try {
        const response = await generateNarrative({
          incident_text: incidentText,
          mode: activeMode,
          safety_graph: safetyGraph,
          causal_chains: causalChains,
          risk_score: riskScore,
          risk_priority: riskPriority,
          sif_potential: sifPotential,
          sif_level: sifLevel,
          life_saving_rule: lifeSavingRule,
          evidence_span: evidenceSpan,
          evidence_terms: evidenceTerms,
          counterfactual_scenario: counterfactualScenario,
          confidence: confidence,
        })
        setNarrative(response)
      } catch (err) {
        console.error('Failed to generate narrative:', err)
      } finally {
        setIsLoading(false)
      }
    }

    loadNarrative()
  }, [
    incidentText,
    activeMode,
    safetyGraph,
    causalChains,
    riskScore,
    riskPriority,
    sifPotential,
    sifLevel,
    lifeSavingRule,
    evidenceSpan,
    counterfactualScenario,
    confidence,
  ])

  const getSourceBasisBadge = (source: string) => {
    switch (source.toUpperCase()) {
      case 'CAUSAL_GRAPH':
        return 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30'
      case 'RISK_ENGINE':
        return 'bg-amber-500/15 text-amber-300 border-amber-500/30'
      case 'COUNTERFACTUAL':
        return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
      case 'EVIDENCE':
        return 'bg-purple-500/15 text-purple-300 border-purple-500/30'
      case 'LSR_MAPPING':
        return 'bg-rose-500/15 text-rose-300 border-rose-500/30'
      default:
        return 'bg-slate-500/15 text-slate-300 border-slate-500/30'
    }
  }

  const getPriorityBadge = (p: string) => {
    switch (p.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/40'
      case 'HIGH':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40'
      case 'MEDIUM':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/40'
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/40'
    }
  }

  return (
    <div className="rounded-2xl bg-slate-900/90 border border-slate-800 p-5 shadow-2xl backdrop-blur-xl space-y-5">
      {/* Top Header & Mode Navigation Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-600 shadow-md shadow-cyan-900/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white tracking-wide">
                AI Safety Narrative & Explainability Layer
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Phase 5E
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Grounded natural language translation of verified deterministic safety findings
            </p>
          </div>
        </div>

        {/* Narrative Mode Selection Tabs */}
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveMode('EXECUTIVE')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeMode === 'EXECUTIVE'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            Executive
          </button>
          <button
            onClick={() => setActiveMode('INVESTIGATION')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeMode === 'INVESTIGATION'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileSearch className="w-3.5 h-3.5" />
            Investigation
          </button>
          <button
            onClick={() => setActiveMode('FIELD')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeMode === 'FIELD'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <HardHat className="w-3.5 h-3.5" />
            Field Alert
          </button>
          <button
            onClick={() => setActiveMode('COUNTERFACTUAL')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeMode === 'COUNTERFACTUAL'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <GitFork className="w-3.5 h-3.5" />
            What-If
            {counterfactualScenario && (
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            )}
          </button>
        </div>
      </div>

      {/* 1. Clear Separation: System-Determined Truth vs AI Translation */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 p-3 rounded-xl bg-slate-950/70 border border-slate-800/80">
        <div>
          <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 flex items-center gap-1">
            <Cpu className="w-3 h-3 text-cyan-400" /> Source of Truth
          </span>
          <div className="text-xs font-mono font-bold text-slate-200 mt-0.5">
            Deterministic Engine
          </div>
        </div>
        <div>
          <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400">
            Composite Risk
          </span>
          <div className="text-xs font-mono font-bold text-amber-300 mt-0.5 flex items-center gap-1.5">
            {riskScore}/100
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-sans">
              {riskPriority}
            </span>
          </div>
        </div>
        <div>
          <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400">
            SIF Precursor
          </span>
          <div className="text-xs font-mono font-bold mt-0.5">
            {sifPotential ? (
              <span className="text-rose-400 flex items-center gap-1">
                <ShieldAlert className="w-3.5 h-3.5" /> {sifLevel} Precursor
              </span>
            ) : (
              <span className="text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Controlled
              </span>
            )}
          </div>
        </div>
        <div>
          <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400">
            Validation Status
          </span>
          <div className="text-xs font-mono mt-0.5 flex items-center gap-1.5">
            {narrative?.validation_status === 'VALID' ? (
              <span className="text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Verified Valid
              </span>
            ) : (
              <span className="text-amber-400 flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" /> Fallback Applied
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 2. Loading Spinner */}
      {isLoading && (
        <div className="py-8 flex flex-col items-center justify-center gap-2 text-slate-400">
          <RefreshCw className="w-5 h-5 animate-spin text-cyan-400" />
          <span className="text-xs">Synthesizing grounded narrative in {activeMode} mode...</span>
        </div>
      )}

      {/* 3. Main Narrative Content */}
      {!isLoading && narrative && (
        <div className="space-y-4">
          {/* Executive / Primary Explanation Box */}
          <div className="p-4 rounded-xl bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 border border-cyan-500/20 shadow-lg relative overflow-hidden">
            <div className="absolute top-0 right-0 p-3 opacity-10">
              <Sparkles className="w-20 h-20 text-cyan-400" />
            </div>
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-cyan-300 mb-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400" />
              {activeMode} Narrative Explanation
            </div>
            <p className="text-sm leading-relaxed text-slate-100 font-sans">
              {narrative.executive_summary}
            </p>
            {narrative.incident_interpretation && (
              <p className="text-xs text-slate-300 leading-relaxed mt-2 pt-2 border-t border-slate-800/80">
                <span className="font-semibold text-slate-200">Interpretation: </span>
                {narrative.incident_interpretation}
              </p>
            )}
          </div>

          {/* Causal Chain Traversal */}
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
            <div className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              Causal Reasoning Chain
            </div>
            <p className="text-xs text-slate-400 leading-relaxed font-mono">
              {narrative.causal_explanation}
            </p>
          </div>

          {/* Barrier Analysis Cards */}
          {narrative.barrier_analysis.length > 0 && (
            <div className="space-y-2">
              <div className="text-xs font-semibold text-slate-300">
                Evaluated Safety Barriers ({narrative.barrier_analysis.length})
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {narrative.barrier_analysis.map((b, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white">{b.control}</span>
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                          b.failure
                            ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                            : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        }`}
                      >
                        {b.observed_status}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 leading-snug">{b.explanation}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Key Findings & Recommended Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Key Findings */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <div className="text-xs font-semibold text-slate-200">Key Safety Findings</div>
              <ul className="space-y-1.5">
                {narrative.key_findings.map((item, idx) => (
                  <li key={idx} className="text-xs text-slate-300 flex items-start gap-1.5">
                    <ArrowRight className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Grounded Recommended Actions */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <div className="text-xs font-semibold text-slate-200">Grounded Recommendations</div>
              <div className="space-y-2">
                {narrative.recommended_actions.map((act, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800/80 space-y-1"
                  >
                    <div className="flex items-center justify-between gap-1">
                      <span className="text-xs font-semibold text-slate-100">{act.action}</span>
                      <div className="flex items-center gap-1 shrink-0">
                        <span
                          className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${getPriorityBadge(
                            act.priority
                          )}`}
                        >
                          {act.priority}
                        </span>
                        <span
                          className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${getSourceBasisBadge(
                            act.source_basis
                          )}`}
                        >
                          {act.source_basis}
                        </span>
                      </div>
                    </div>
                    <p className="text-[11px] text-slate-400">{act.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Grounding Provenance Inspection Drawer */}
          <div className="pt-2 border-t border-slate-800 flex flex-col gap-2">
            <button
              onClick={() => setShowGrounding(!showGrounding)}
              className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center justify-between py-1 transition-colors"
            >
              <span className="flex items-center gap-1.5">
                <HelpCircle className="w-3.5 h-3.5" />
                Inspect Mathematical Grounding & Provenance ({narrative.grounding.length} claims)
              </span>
              <span className="text-[11px] text-slate-400">
                {showGrounding ? 'Hide Details' : 'Show Details'}
              </span>
            </button>

            {showGrounding && (
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="text-[11px] text-slate-400">
                  Every claim is verified against deterministic safety components before presentation:
                </div>
                <div className="space-y-1.5">
                  {narrative.grounding.map((g, idx) => (
                    <div
                      key={idx}
                      className="p-2 rounded bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs"
                    >
                      <span className="text-slate-300">{g.claim}</span>
                      <div className="flex items-center gap-1.5 shrink-0">
                        <span
                          className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${getSourceBasisBadge(
                            g.source_type
                          )}`}
                        >
                          {g.source_type}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400">
                          {g.source_reference}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="text-[10px] text-slate-500 pt-1 flex items-center gap-2">
                  <Clock className="w-3 h-3" />
                  Generated in {narrative.latency_ms.toFixed(2)}ms via{' '}
                  <span className="font-mono text-slate-400">{narrative.model_name}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

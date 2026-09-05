import { useState, useEffect } from 'react'
import type { AnalysisResponse, CounterfactualScenario } from '../../types/analysis'
import { analyzeText, generateFallbackAnalysis } from '../../services/api'
import { IncidentInput, PRESET_SCENARIOS } from './IncidentInput'
import { RiskScoreWidget } from './RiskScoreWidget'
import { CausalSafetyGraph } from '../causal-graph/CausalSafetyGraph'
import { SafetyNarrativePanel } from '../narrative/SafetyNarrativePanel'
import { CorrectiveActionPanel } from '../interventions/CorrectiveActionPanel'
import { AlertTriangle, Network, Sparkles, Wrench, GitFork } from 'lucide-react'

export const AnalysisDashboard = () => {
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null)
  const [currentText, setCurrentText] = useState<string>(PRESET_SCENARIOS[0].text)
  const [activeScenario, setActiveScenario] = useState<CounterfactualScenario | null>(null)
  const [activeViewTab, setActiveViewTab] = useState<'causal' | 'narrative' | 'interventions'>('interventions')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Initialize with the first scenario on initial load
  useEffect(() => {
    handleRunAnalysis(PRESET_SCENARIOS[0].text)
  }, [])

  const handleRunAnalysis = async (text: string) => {
    setIsLoading(true)
    setError(null)
    setCurrentText(text)
    setActiveScenario(null)
    try {
      const result = await analyzeText(text)
      setAnalysis(result)
    } catch (err: any) {
      console.error('Analysis error:', err)
      setError(err.message || 'Failed to analyze safety report.')
      // Graceful fallback to maintain UI usability
      setAnalysis(generateFallbackAnalysis(text))
    } finally {
      setIsLoading(false)
    }
  }

  const handleSimulateBarrierFromIntervention = (_barrierName: string) => {
    // Switch to causal graph / counterfactual tab
    setActiveViewTab('causal')
  }


  return (
    <div className="space-y-6">
      {/* 1. Incident Input & Scenario Trigger */}
      <IncidentInput onAnalyze={handleRunAnalysis} isLoading={isLoading} />

      {error && (
        <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>Notice: {error} (Rendered using deterministic local reasoning engine)</span>
        </div>
      )}

      {/* 2. Analysis Results & Causal Intelligence View */}
      {analysis && (
        <div className="space-y-6">
          {/* Risk & Classification Metric Cards */}
          <RiskScoreWidget
            risk={analysis.risk}
            sifPotential={analysis.sif_potential}
            sifLevel={analysis.sif_level}
            lsr={analysis.life_saving_rule}
            probability={analysis.model_probability}
          />

          {/* Tab Navigation Toolbar for Analysis Layers */}
          <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/90 border border-slate-800 p-2 rounded-2xl">
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setActiveViewTab('interventions')}
                className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                  activeViewTab === 'interventions'
                    ? 'bg-gradient-to-r from-amber-600 to-orange-600 text-white shadow-md shadow-orange-950/40'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Wrench className="w-4 h-4" />
                <span>Corrective Actions & Prevention (Phase 5F)</span>
              </button>

              <button
                onClick={() => setActiveViewTab('causal')}
                className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                  activeViewTab === 'causal'
                    ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-md shadow-cyan-950/40'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <GitFork className="w-4 h-4" />
                <span>Causal Safety Graph & Simulation (Phase 5C/5D)</span>
              </button>

              <button
                onClick={() => setActiveViewTab('narrative')}
                className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                  activeViewTab === 'narrative'
                    ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-md shadow-indigo-950/40'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Sparkles className="w-4 h-4" />
                <span>AI Safety Narrative (Phase 5E)</span>
              </button>
            </div>

            <span className="text-[11px] font-mono text-slate-400 px-3 hidden md:inline">
              Deterministic Safety Engine Active
            </span>
          </div>

          {/* Tab Content Display */}
          {activeViewTab === 'interventions' && (
            <CorrectiveActionPanel
              analysis={analysis}
              onSimulateIntervention={handleSimulateBarrierFromIntervention}
            />
          )}

          {activeViewTab === 'narrative' && (
            <SafetyNarrativePanel
              incidentText={currentText || analysis.report_text || ''}
              safetyGraph={analysis.safety_graph}
              causalChains={analysis.causal_chains}
              riskScore={analysis.risk?.score ?? 85}
              riskPriority={analysis.risk?.priority ?? 'CRITICAL'}
              sifPotential={analysis.sif_potential}
              sifLevel={analysis.sif_level}
              lifeSavingRule={analysis.life_saving_rule}
              evidenceSpan={analysis.evidence_span}
              evidenceTerms={analysis.evidence_terms}
              counterfactualScenario={activeScenario}
              confidence={analysis.overall_confidence}
            />
          )}

          {activeViewTab === 'causal' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between pt-2 border-t border-slate-800">
                <div className="flex items-center gap-2">
                  <Network className="w-5 h-5 text-cyan-400" />
                  <h2 className="text-base font-bold text-white tracking-tight">
                    Explainable Causal Safety Reasoning & Simulation Engine
                  </h2>
                </div>
                <span className="text-xs font-mono text-slate-400">
                  Phase 5C Visualizer • Phase 5D Counterfactuals
                </span>
              </div>

              <CausalSafetyGraph
                safetyGraph={analysis.safety_graph}
                causalChains={analysis.causal_chains}
                reasoningSummary={analysis.reasoning_summary}
                sifPotential={analysis.sif_potential}
                overallConfidence={analysis.overall_confidence}
                riskScore={analysis.risk?.score ?? 85}
                reportText={currentText}
                onScenarioChange={(sc) => setActiveScenario(sc)}
              />
            </div>
          )}
        </div>
      )}
    </div>
  )
}



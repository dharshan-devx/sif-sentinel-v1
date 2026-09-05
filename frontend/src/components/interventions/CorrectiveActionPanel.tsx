import React, { useState, useEffect } from 'react'
import {
  Wrench,
  CheckCircle,
  XCircle,
  Filter,
  Play,
  RotateCcw,
} from 'lucide-react'
import type {
  AnalysisResponse,
  InterventionAnalysisResponse,
  HierarchyLevel,
} from '../../types/analysis'
import { analyzeInterventions } from '../../services/api'
import { CumulativePreventionMatrix } from './CumulativePreventionMatrix'


interface CorrectiveActionPanelProps {
  analysis: AnalysisResponse
  onSimulateIntervention?: (barrierName: string) => void
}

export const CorrectiveActionPanel: React.FC<CorrectiveActionPanelProps> = ({
  analysis,
  onSimulateIntervention,
}) => {
  const [data, setData] = useState<InterventionAnalysisResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [selectedFilter, setSelectedFilter] = useState<'ALL' | HierarchyLevel>('ALL')
  const [reviewDecisions, setReviewDecisions] = useState<
    Record<string, { status: 'APPROVED' | 'REJECTED' | 'MODIFIED'; notes?: string }>
  >({})

  // Fetch or compute interventions when analysis changes
  useEffect(() => {
    let isMounted = true
    setLoading(true)

    analyzeInterventions({
      safety_graph: analysis.safety_graph,
      risk_score: analysis.risk?.score ?? 85,
      risk_priority: analysis.risk?.priority ?? 'HIGH',
      life_saving_rule: analysis.life_saving_rule,
      sif_level: analysis.sif_level,
    })
      .then((res) => {
        if (isMounted) {
          setData(res)
          setLoading(false)
        }
      })
      .catch(() => {
        if (isMounted) {
          setLoading(false)
        }
      })

    return () => {
      isMounted = false
    }
  }, [analysis])

  const handleDecision = (
    recId: string,
    decision: 'APPROVED' | 'REJECTED' | 'MODIFIED',
    notes?: string
  ) => {
    setReviewDecisions((prev) => ({
      ...prev,
      [recId]: { status: decision, notes },
    }))
  }

  const getHierarchyBadge = (level: string) => {
    switch (level) {
      case 'ELIMINATION':
        return {
          bg: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
          label: '1. Elimination',
        }
      case 'SUBSTITUTION':
        return {
          bg: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
          label: '2. Substitution',
        }
      case 'ENGINEERING_CONTROL':
        return {
          bg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
          label: '3. Engineering Control',
        }
      case 'ADMINISTRATIVE_CONTROL':
        return {
          bg: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
          label: '4. Administrative Control',
        }
      case 'PPE':
        return {
          bg: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
          label: '5. PPE',
        }
      default:
        return {
          bg: 'bg-slate-800 text-slate-300 border-slate-700',
          label: level,
        }
    }
  }

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'CRITICAL':
        return 'bg-red-500/20 text-red-300 border-red-500/40 animate-pulse'
      case 'HIGH':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40'
      case 'MEDIUM':
        return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40'
      default:
        return 'bg-slate-700/50 text-slate-300 border-slate-600'
    }
  }

  if (loading) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-12 text-center space-y-4 backdrop-blur-md">
        <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-slate-400 font-mono">
          Evaluating deterministic Hierarchy of Controls & Multi-Barrier prevention plan...
        </p>
      </div>
    )
  }

  if (!data || data.recommendations.length === 0) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-8 text-center space-y-3">
        <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto" />
        <div className="text-sm font-bold text-white">All Identified Barriers Verified</div>
        <p className="text-xs text-slate-400 max-w-md mx-auto">
          No critical barrier failures or degradation detected in this operational sequence. Standard safety precautions apply.
        </p>
      </div>
    )
  }

  const filteredRecs =
    selectedFilter === 'ALL'
      ? data.recommendations
      : data.recommendations.filter((r) => r.hierarchy_level === selectedFilter)

  return (
    <div className="space-y-6">
      {/* Top Banner & Control Filters */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-tr from-amber-600 to-orange-600 shadow-lg shadow-orange-900/30 flex items-center justify-center">
              <Wrench className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                Automated Corrective Intervention Intelligence
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  Phase 5F • Rule-Derived
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Standardized, prioritized safety barrier restoration actions derived from causal graph failures.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 bg-slate-950/80 p-1.5 rounded-xl border border-slate-800">
            <Filter className="w-3.5 h-3.5 text-slate-400 ml-1.5" />
            {(['ALL', 'ENGINEERING_CONTROL', 'ADMINISTRATIVE_CONTROL'] as const).map((filter) => (
              <button
                key={filter}
                onClick={() => setSelectedFilter(filter)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                  selectedFilter === filter
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {filter === 'ALL'
                  ? `All Actions (${data.total_recommendations})`
                  : filter === 'ENGINEERING_CONTROL'
                  ? 'Engineering'
                  : 'Administrative'}
              </button>
            ))}
          </div>
        </div>

        {/* Advisory Distinction Note */}
        <div className="flex items-center gap-2 text-[11px] text-slate-400 bg-slate-950/40 px-3.5 py-2 rounded-xl border border-slate-800/60">
          <span className="w-2 h-2 rounded-full bg-cyan-400" />
          <span>
            <strong className="text-slate-300">System Governance:</strong> Recommendations are deterministic decision-support advisories. Official action sign-off requires human HSE approval.
          </span>
        </div>
      </div>

      {/* Recommendations Card List */}
      <div className="space-y-4">
        {filteredRecs.map((rec) => {
          const hierBadge = getHierarchyBadge(rec.hierarchy_level)
          const decision = reviewDecisions[rec.id]

          return (
            <div
              key={rec.id}
              className={`bg-slate-900/90 border rounded-2xl p-5 space-y-4 shadow-lg transition-all ${
                decision?.status === 'APPROVED'
                  ? 'border-emerald-500/60 bg-emerald-950/10'
                  : decision?.status === 'REJECTED'
                  ? 'border-red-500/40 opacity-70'
                  : 'border-slate-800 hover:border-slate-700'
              }`}
            >
              {/* Card Header */}
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={`text-[10px] font-mono font-bold px-2.5 py-1 rounded-md border ${getPriorityBadge(
                      rec.priority
                    )}`}
                  >
                    {rec.priority} ({rec.priority_score} pts)
                  </span>
                  <span
                    className={`text-[10px] font-semibold px-2.5 py-1 rounded-md border ${hierBadge.bg}`}
                  >
                    {hierBadge.label}
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                    {rec.action_type.replace(/_/g, ' ')}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-slate-500">
                    Rule: {rec.deterministic_rule_id}
                  </span>
                </div>
              </div>

              {/* Title & Description */}
              <div className="space-y-1.5">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  {rec.title}
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {rec.description}
                </p>
              </div>

              {/* Rationale & Linked Causal Context */}
              <div className="bg-slate-950/70 rounded-xl p-3 border border-slate-800/80 space-y-2 text-xs">
                <div className="text-slate-400 leading-relaxed">
                  <strong className="text-slate-300">Deterministic Rationale: </strong>
                  {rec.rationale}
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 border-t border-slate-800/60 text-[11px] text-slate-400 font-mono">
                  <div>
                    <span className="text-slate-500 block text-[9px] uppercase">Target Barrier:</span>
                    <span className="text-cyan-300 font-semibold">{rec.linked_barrier}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[9px] uppercase">Observed State:</span>
                    <span className="text-red-400 font-semibold">{rec.current_barrier_status}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[9px] uppercase">Predicted Delta:</span>
                    <span className="text-emerald-400 font-semibold">{rec.predicted_risk_delta} pts</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[9px] uppercase">Timeframe:</span>
                    <span className="text-amber-300 font-semibold">{rec.implementation_timeframe}</span>
                  </div>
                </div>
              </div>

              {/* Action Toolbar: What-If Simulation + Human Review */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-800/60">
                <div className="flex items-center gap-2">
                  {onSimulateIntervention && (
                    <button
                      onClick={() => onSimulateIntervention(rec.linked_barrier)}
                      className="px-3 py-1.5 rounded-xl bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 text-xs font-semibold flex items-center gap-1.5 transition-colors border border-cyan-500/40"
                    >
                      <Play className="w-3.5 h-3.5 fill-cyan-300" />
                      Simulate This Intervention
                    </button>
                  )}
                </div>

                {/* Human Review Decision Buttons */}
                <div className="flex items-center gap-2">
                  {decision ? (
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-xs font-bold px-2.5 py-1 rounded-lg border ${
                          decision.status === 'APPROVED'
                            ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                            : decision.status === 'MODIFIED'
                            ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                            : 'bg-red-500/20 text-red-300 border-red-500/40'
                        }`}
                      >
                        {decision.status === 'APPROVED' && '✓ Approved Action'}
                        {decision.status === 'MODIFIED' && '✎ Modified Action'}
                        {decision.status === 'REJECTED' && '✕ Rejected Action'}
                      </span>
                      <button
                        onClick={() =>
                          setReviewDecisions((prev) => {
                            const copy = { ...prev }
                            delete copy[rec.id]
                            return copy
                          })
                        }
                        className="p-1 rounded text-slate-500 hover:text-slate-300"
                        title="Reset decision"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ) : (
                    <>
                      <button
                        onClick={() => handleDecision(rec.id, 'APPROVED')}
                        className="px-3 py-1.5 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 text-xs font-semibold flex items-center gap-1 transition-colors border border-emerald-500/40"
                      >
                        <CheckCircle className="w-3.5 h-3.5" />
                        Approve Action
                      </button>
                      <button
                        onClick={() => handleDecision(rec.id, 'REJECTED', 'Operator verified in field')}
                        className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 text-xs font-semibold flex items-center gap-1 transition-colors border border-slate-700"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        Reject
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Multi-Barrier Cumulative Prevention Matrix Section */}
      {data.cumulative_prevention_plan && (
        <CumulativePreventionMatrix
          plan={data.cumulative_prevention_plan}
          onSimulateStep={onSimulateIntervention}
        />
      )}
    </div>
  )
}

export type BarrierStatus =
  | 'VERIFIED'
  | 'NOT_VERIFIED'
  | 'PERFORMED'
  | 'NOT_PERFORMED'
  | 'FAILED'
  | 'BYPASSED'
  | 'MISSING'
  | 'EXPIRED'
  | 'UNKNOWN'

export type SIFLevel = 'PSIF' | 'SIF' | 'NON_SIF'

export type NodeType =
  | 'ACTIVITY'
  | 'HAZARD'
  | 'CONTROL'
  | 'STATUS'
  | 'EXPOSURE'
  | 'PRECURSOR'
  | 'EVIDENCE'

export interface RiskComponent {
  name: string
  score: number
  reason: string
}

export interface RiskDetail {
  score: number
  priority: string
  components: RiskComponent[]
  version: string
}

export interface EvidenceGrounding {
  claim: string
  evidence: string
  source_span: [number, number] | null
  evidence_type: string
  confidence: number
}

export interface ConfidenceBreakdown {
  model_confidence?: number
  extraction_confidence?: number
  relationship_confidence?: number
  evidence_confidence?: number
  overall_reasoning_confidence?: number
  [key: string]: number | undefined
}

export interface CausalChain {
  activity: string
  hazard: string
  control: string
  control_status: BarrierStatus
  barrier_failure: boolean
  exposure: string
  relationship: string
  evidence: EvidenceGrounding[]
  confidence: number
  confidence_breakdown?: ConfidenceBreakdown
  source_span?: [number, number] | null
  temporal_inversion?: boolean
  negation_detected?: boolean
  prevention_detected?: boolean
}

export interface GraphNode {
  id: string
  type: NodeType
  label: string
  status?: BarrierStatus | string
  confidence?: number
  evidence?: string
  source_span?: [number, number] | null
  source_text?: string
  metadata?: Record<string, any>
  properties?: Record<string, any>
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  relationship: string
  label?: string
  confidence?: number
}

export interface SafetyReasoningGraph {
  nodes: GraphNode[]
  edges: GraphEdge[]
  causal_chains: CausalChain[]
  summary?: string
  barrier_failure_detected?: boolean
  high_energy_hazard_present?: boolean
  precursor_detected?: boolean
}

export interface AnalysisResponse {
  report_id?: string | null
  analysis_id?: string | null
  report_text?: string
  sif_potential: boolean
  sif_level: SIFLevel
  model_probability: number
  activity?: string | null
  hazard?: string | null
  barrier?: string | null
  barrier_status: BarrierStatus
  barrier_failure?: string | null
  life_saving_rule?: string | null
  rule_confidence: number
  evidence_span?: string | null
  evidence_sentences: string[]
  evidence_terms: string[]
  overall_confidence: number
  review_required: boolean
  model_version: string
  explanation: string
  risk?: RiskDetail | null

  // Phase 5B Causal Reasoning Metadata
  safety_graph?: SafetyReasoningGraph | null
  causal_chains?: CausalChain[] | null
  reasoning_summary?: string | null

  // Phase 5F Corrective Interventions & Prevention Plan
  interventions?: InterventionItem[] | null
  prevention_plan?: CumulativePreventionPlan | null

  // Phase J: LLM Assistive Metadata
  reviewer_summary?: string | null
  llm_attempted?: boolean
  llm_used?: boolean
  llm_provider?: string | null
  llm_model_used?: string | null
  llm_timestamp?: string | null
  llm_error_code?: string | null
}

// Phase 5D Counterfactual Simulation Types
export interface CounterfactualChange {
  element_type: string
  element_name: string
  observed_value: any
  simulated_value: any
  description: string
}

export interface CounterfactualScenario {
  scenario_id: string
  target_node_id?: string | null
  target_control: string
  original_status: string
  simulated_status: string
  original_barrier_failure: boolean
  simulated_barrier_failure: boolean
  original_exposure: string
  simulated_exposure: string
  original_risk_score: number
  simulated_risk_score: number
  risk_delta: number
  risk_direction: 'REDUCED' | 'UNCHANGED' | 'INCREASED'
  original_sif_potential: boolean
  simulated_sif_potential: boolean
  original_sif_classification: string
  simulated_sif_classification: string
  causal_changes: CounterfactualChange[]
  affected_nodes: string[]
  affected_edges: Record<string, any>[]
  assumptions: string[]
  interpretation: string
  confidence: number
  simulated_graph: SafetyReasoningGraph
  simulation_only: boolean
  created_at: string
}

export interface CounterfactualRequest {
  report_text?: string
  target_control: string
  target_node_id?: string | null
  simulated_status?: string
  safety_graph?: SafetyReasoningGraph | null
  causal_chains?: CausalChain[] | null
  risk_score?: number | null
  has_lsr?: boolean
  precursor_priority?: string | null
}

// Phase 5E LLM Narrative Translation Types
export type NarrativeMode = 'EXECUTIVE' | 'INVESTIGATION' | 'FIELD' | 'COUNTERFACTUAL'

export type SourceBasis =
  | 'CAUSAL_GRAPH'
  | 'RISK_ENGINE'
  | 'COUNTERFACTUAL'
  | 'EVIDENCE'
  | 'LSR_MAPPING'

export type ValidationStatus = 'VALID' | 'FALLBACK_APPLIED' | 'REJECTED'

export interface BarrierAnalysisItem {
  control: string
  observed_status: string
  failure: boolean
  explanation: string
  source_basis: SourceBasis | string
}

export interface RecommendedActionItem {
  action: string
  reason: string
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | string
  source_basis: SourceBasis | string
  target_control?: string | null
}

export interface GroundingItem {
  claim: string
  source_type: SourceBasis | string
  source_reference: string
}

export interface NarrativeRequest {
  incident_text: string
  mode?: NarrativeMode
  safety_graph?: SafetyReasoningGraph | null
  causal_chains?: CausalChain[] | null
  risk_score?: number | null
  risk_priority?: string | null
  sif_potential?: boolean | null
  sif_level?: string | null
  life_saving_rule?: string | null
  evidence_span?: string | null
  evidence_terms?: string[]
  counterfactual_scenario?: CounterfactualScenario | null
  confidence?: number | null
}

export interface NarrativeResponse {
  mode: NarrativeMode | string
  executive_summary: string
  incident_interpretation: string
  causal_explanation: string
  barrier_analysis: BarrierAnalysisItem[]
  sif_explanation: string
  risk_explanation: string
  lsr_explanation?: string | null
  key_findings: string[]
  recommended_actions: RecommendedActionItem[]
  counterfactual_explanation?: string | null
  confidence_statement: string
  limitations: string[]
  grounding: GroundingItem[]
  validation_status: ValidationStatus | string
  validation_errors?: string[]
  provider_name: string
  model_name: string
  latency_ms: number
  generated_at: string
}

// Phase 5F: Corrective Intervention & Prevention Types
export type HierarchyLevel =
  | 'ELIMINATION'
  | 'SUBSTITUTION'
  | 'ENGINEERING_CONTROL'
  | 'ADMINISTRATIVE_CONTROL'
  | 'PPE'

export type InterventionActionType =
  | 'IMMEDIATE_STOP_WORK'
  | 'BARRIER_RESTORATION'
  | 'ENGINEERING_INSTALL'
  | 'ENGINEERING_UPGRADE'
  | 'VERIFICATION_AUDIT'
  | 'PERMIT_VERIFY'
  | 'ISOLATION_VERIFY'
  | 'INSPECTION'
  | 'CALIBRATION'
  | 'PREVENTIVE_TRAINING'
  | 'SUPERVISORY_OVERSIGHT'
  | 'PROCEDURE_REVISION'
  | 'PPE_ENHANCEMENT'

export type InterventionPriority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'

export interface InterventionItem {
  id: string
  intervention_code: string
  title: string
  description: string
  hierarchy_level: HierarchyLevel | string
  action_type: InterventionActionType | string
  priority: InterventionPriority | string
  priority_score: number
  urgency: string
  rationale: string
  linked_hazard: string
  linked_activity: string
  linked_barrier: string
  target_node_id?: string | null
  current_barrier_status: string
  target_barrier_status: string
  predicted_original_risk: number
  predicted_simulated_risk: number
  predicted_risk_delta: number
  feasibility_score: string
  implementation_timeframe: string
  required_lsr?: string | null
  source_basis: string
  deterministic_rule_id: string
  confidence: number
  status: string
  created_at: string
}

export interface PreventionTrajectoryStep {
  step_number: number
  barrier_name: string
  action_title: string
  simulated_risk_score: number
  step_risk_delta: number
  cumulative_risk_delta: number
  residual_sif_potential: boolean
}

export interface CumulativePreventionPlan {
  plan_id: string
  baseline_risk: number
  target_risk: number
  total_risk_delta: number
  defense_in_depth_layers: string[]
  trajectory: PreventionTrajectoryStep[]
  primary_mitigation: string
  secondary_mitigation?: string | null
  residual_risk_level: string
  assumptions: string[]
}

export interface InterventionAnalysisRequest {
  incident_text?: string
  safety_graph?: SafetyReasoningGraph | null
  risk_score?: number | null
  risk_priority?: string | null
  life_saving_rule?: string | null
  sif_level?: string | null
}

export interface InterventionAnalysisResponse {
  total_recommendations: number
  overall_hierarchy_level: string
  baseline_risk_score: number
  target_risk_score: number
  cumulative_risk_delta: number
  recommendations: InterventionItem[]
  cumulative_prevention_plan: CumulativePreventionPlan
  source_basis: string
  deterministic: boolean
  generated_at: string
}



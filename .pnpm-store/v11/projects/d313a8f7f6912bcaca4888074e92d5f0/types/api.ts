export type UserRole = "ADMIN" | "HSE_MANAGER" | "HSE_ANALYST" | "REVIEWER" | "VIEWER";
export type ReportType = "UNSAFE_ACT" | "UNSAFE_CONDITION" | "NEAR_MISS" | "INCIDENT";
export type SourceType = "PUBLIC" | "SYNTHETIC" | "USER_SUBMITTED" | "IMPORTED";
export type ReportStatus = "NEW" | "ANALYZED" | "REVIEW_REQUIRED" | "REVIEWED" | "CLOSED";
export type SIFLevel = "NON_SIF" | "LOW" | "MEDIUM" | "HIGH" | "REVIEW";
export type BarrierStatus = "EFFECTIVE" | "FAILED" | "MISSING" | "UNKNOWN";
export type ReviewDecision = "PENDING" | "APPROVE" | "REJECT" | "MODIFY";
export type InterventionReviewStatus = "PENDING" | "ACCEPTED" | "MODIFIED" | "REJECTED";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse { access_token: string; token_type: "bearer"; user: User }
export interface LoginRequest { email: string; password: string }
export interface RegisterRequest { email: string; password: string; full_name: string }

export interface Site {
  id: string;
  name: string;
  code: string;
  location: string;
  region: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
export interface SiteCreate {
  name: string; code: string; location: string; region: string;
  description?: string | null; is_active?: boolean;
}
export type SiteUpdate = Partial<Omit<SiteCreate, "code">>;

export interface Report {
  id: string;
  report_id: string;
  report_type: ReportType;
  report_text: string;
  site_id: string;
  location: string;
  department: string;
  activity: string | null;
  reported_at: string;
  source_type: SourceType;
  status: ReportStatus;
  created_by: string;
  created_at: string;
  updated_at: string;
}
export interface ReportCreate {
  report_id?: string;
  report_type: ReportType;
  report_text: string;
  site_id: string;
  location: string;
  department: string;
  activity?: string | null;
  reported_at: string;
  source_type: SourceType;
}
export interface ReportUpdate {
  report_text?: string; location?: string; department?: string;
  activity?: string | null; status?: ReportStatus;
}
export interface ReportPage { items: Report[]; total: number; page: number; page_size: number }

export interface RiskComponent { name: string; score: number; reason: string }
export interface RiskDetail { score: number; priority: string; components: RiskComponent[]; version: string }
export interface AnalysisResponse {
  report_id: string | null;
  analysis_id: string | null;
  sif_potential: boolean;
  sif_level: SIFLevel;
  model_probability: number;
  activity: string | null;
  hazard: string | null;
  barrier: string | null;
  barrier_status: BarrierStatus;
  barrier_failure: string | null;
  life_saving_rule: string | null;
  rule_confidence: number;
  evidence_span: string | null;
  evidence_sentences: string[];
  evidence_terms: string[];
  overall_confidence: number;
  review_required: boolean;
  model_version: string;
  explanation: string;
  risk: RiskDetail | null;
  reviewer_summary: string | null;
  llm_attempted: boolean;
  llm_used: boolean;
  llm_provider: string | null;
  llm_model_used: string | null;
  llm_timestamp: string | null;
  llm_error_code: string | null;
}

export interface ReviewQueueItem {
  id: string; report_id: string; decision: ReviewDecision;
  reviewer_id: string | null; reviewed_at: string | null; report_text: string;
  evidence_span: string | null; overall_confidence: number | null;
  explanation: string | null; reviewer_comment: string | null;
  corrected_sif_level: SIFLevel | null; corrected_activity: string | null;
  corrected_hazard: string | null; corrected_barrier: string | null;
  corrected_barrier_status: BarrierStatus | null; corrected_barrier_failure: string | null;
  corrected_life_saving_rule: string | null;
}
export interface ReviewDecisionRequest {
  decision: ReviewDecision; corrected_sif_level?: SIFLevel | null;
  corrected_activity?: string | null; corrected_hazard?: string | null;
  corrected_barrier?: string | null; corrected_barrier_status?: BarrierStatus | null;
  corrected_barrier_failure?: string | null; corrected_life_saving_rule?: string | null;
  reviewer_comment?: string | null;
}
export interface DecisionResponse {
  review_id: string; decision: ReviewDecision; report_id: string; report_status: string;
  reviewer_id: string; reviewed_at: string; message: string;
}

export interface InterventionRead {
  id: string; report_id: string | null; precursor_pattern_id: string | null;
  intervention_rule_id: string; category: string; title: string; description: string;
  rationale: string; priority: string; action_type: string; review_required: boolean;
  evidence_snapshot: Record<string, unknown>; source_rule: string; engine_version: string;
  risk_priority: string | null; life_saving_rule: string | null;
  review_status: InterventionReviewStatus; reviewed_by: string | null; reviewed_at: string | null;
  reviewer_comments: string | null; reviewer_title: string | null;
  reviewer_description: string | null; reviewer_rationale: string | null; created_at: string;
}
export interface InterventionReviewRequest {
  decision: InterventionReviewStatus; reviewer_comments?: string | null;
  reviewer_title?: string | null; reviewer_description?: string | null;
  reviewer_rationale?: string | null;
}
export interface InterventionSummary { total: number; critical: number; pending: number; by_category: Record<string, number> }

export interface PrecursorSummary {
  id: string; category: string; activity: string; hazard: string; barrier: string;
  failure_type: string; occurrence_count: number; sif_count: number; sif_density: number;
  recent_count: number; site_count: number; department_count: number; trend: string;
  risk_score: number; priority: string; first_seen: string | null; last_seen: string | null;
  why_it_matters: string;
}
export interface PrecursorDetail extends PrecursorSummary {
  sites: string[]; departments: string[];
  representative_reports: Array<{ report_id: string; reported_at: string; site_name: string; department: string; sif_level: string | null }>;
}
export interface PrecursorGraph {
  nodes: Array<{ id: string; label: string; type: string; statistics: Record<string, string | number> }>;
  edges: Array<{ source: string; target: string; label: string }>;
}
export interface RiskItem {
  name: string; report_count: number; sif_count: number; sif_density: number;
  barrier_failure_count: number; risk_score: number; risk_level: string; explanation: string;
}
export interface SiteRiskItem extends RiskItem {
  site_id: string; total_reports: number; sif_reports: number; sif_rate: number;
  high_risk_reports: number; active_precursor_patterns: number; recent_reports: number;
}
export interface BarrierRiskItem {
  barrier: string; total_occurrences: number; failed_count: number; failure_rate: number;
  associated_sif_count: number; risk_score: number; risk_level: string; explanation: string;
}
export interface DashboardSummary {
  total_reports: number; total_sif_reports: number; high_risk_reports: number;
  review_required: number; active_precursors: number; sites_monitored: number;
  sif_rate: number; high_risk_rate: number;
}
export interface TimeSeriesPoint { date: string; total_reports: number; sif_reports: number; high_sif_reports: number; sif_rate: number }
export interface DistributionItem { name: string; count: number; sif_count: number; sif_density: number; percentage: number }
export interface BarrierFailurePoint { date: string; failed_count: number }
export interface MessageResponse { message: string }
export interface LifeSavingRule {
  id: string; code: string; name: string; description: string; keywords: string[];
  hazards: string[]; barriers: string[]; is_active: boolean; created_at: string; updated_at: string;
}
export interface RuleAnalytics { life_saving_rule: string; total_reports: number; sif_reports: number; sif_density: number }

export interface BackendErrorBody {
  success: false;
  error: { code: string; message: string; details: unknown };
  request_id: string | null;
}

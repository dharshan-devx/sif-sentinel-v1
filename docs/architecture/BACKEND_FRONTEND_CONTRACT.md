# SIF SENTINEL — Backend / Frontend Contract

**Status:** reconciled with the backend source and generated OpenAPI on 2026-09-05.
**Contract base URL:** `http://<host>:8000/api/v1`  
**Machine-readable source of truth:** `GET /openapi.json` on the running backend (Swagger UI is normally at `/docs`).

This is the implementation-grounded handoff for a future frontend. The
`frontend/` directory is currently empty. The UI must consume REST only. It must never access PostgreSQL,
import backend Python, infer results from model artefacts, or treat LLM text as
an authoritative safety decision.

## 1. What the system does

SIF Sentinel is a FastAPI modular monolith that receives unsafe-act, unsafe-
condition, near-miss, and incident reports. A persisted report can be analysed
by a deterministic pipeline which extracts activity, hazard, barrier, failure,
evidence and Life-Saving Rule (LSR); classifies SIF potential and level; creates
current precursor candidates; calculates a risk score; optionally queues human
review; rebuilds recurring precursor patterns; and produces a deterministic,
advisory intervention recommendation.

The optional Gemini integration produces **only** `reviewer_summary` and LLM
provenance. It cannot change evidence, SIF, LSR, barrier, precursor, risk,
review routing, or intervention source data.

```text
Browser
  -> Next.js UI
  -> FastAPI /api/v1
       -> JWT/RBAC + request-id middleware
       -> services and deterministic NLP / risk / precursor / intervention engines
       -> SQLAlchemy async session -> PostgreSQL (production) or SQLite (test/dev)
       -> optional Gemini reviewer-summary call (additive only)
```

There is no WebSocket, Server-Sent Events, job queue, file-upload API, or
browser-to-database path in the current backend. Analysis is synchronous: keep
the submit/analyse controls pending until the HTTP response returns.

## 2. Runtime and integration setup

| Concern | Actual contract |
|---|---|
| API prefix | Every business route is under `/api/v1`; no trailing-slash convention is required by the UI. |
| Local backend | `uv run uvicorn app.main:app --reload` from `backend/`; Docker publishes port `8000`. |
| UI origin | Backend default `CORS_ORIGINS` is only `http://localhost:3000`. Set a comma-separated allow-list before deploying a UI at another origin. |
| Credentials | Send `Authorization: Bearer <access_token>` on all non-public business calls. Do not rely on cookies. |
| Token | JWT HS256 with `sub` (user UUID) and `exp`; default expiry is 60 minutes. There is no refresh-token, logout, password-reset, or token-revocation endpoint. |
| Dates | Send ISO-8601 datetimes with a timezone, e.g. `2026-09-03T10:30:00Z`. UUIDs are strings. |
| Pagination | Reports use `{items,total,page,page_size}`. Reviews accept `page` and `page_size` but return a bare array (no total). Intervention lists are not paginated. |
| Caching/realtime | No cache validators or push events. After mutations, refetch the affected resource/list/dashboard query. |
| API client | Use one typed client with `NEXT_PUBLIC_API_BASE_URL`, `Accept: application/json`, JSON body serialization, token injection, and a normalised error type. Never expose `JWT_SECRET_KEY` or `LLM_API_KEY` to the browser. |

The root `docker-compose.yml` provides PostgreSQL 16 and the backend. The
database is not published to the host; the browser should use only the backend
port.

## 3. Authentication, users, and role-based access

### Public endpoints

| Method/path | Request | Successful response |
|---|---|---|
| `POST /auth/register` | `{email, password, full_name}`; password is 12–128 chars | `201 UserRead` |
| `POST /auth/login` | `{email, password}` | `TokenResponse` |
| `GET /health` | none | `{status:"ok",service:"sif-backend"}` |
| `GET /health/status` | none | app/model diagnostic object; it does not test database connectivity |
| `GET /health/ready` | none | readiness response; this is the database readiness probe |

`TokenResponse` is:

```json
{
  "access_token": "<JWT>",
  "token_type": "bearer",
  "user": {
    "id": "uuid", "email": "name@example.com", "full_name": "Name",
    "role": "VIEWER", "is_active": true,
    "created_at": "ISO-8601", "updated_at": "ISO-8601"
  }
}
```

Newly registered users are `VIEWER`. There is currently no user-list, role-
assignment, role-change, invitation, password-reset, or deactivation API, so
role provisioning is an operational/backend concern rather than a frontend
screen.

### Roles and navigation authority

| Capability | ADMIN | HSE_MANAGER | HSE_ANALYST | REVIEWER | VIEWER |
|---|:---:|:---:|:---:|:---:|:---:|
| Read reports, sites, dashboards, risk, precursors, LSRs, interventions | yes | yes | yes | yes | yes |
| Create/update report; run direct or persisted analysis | yes | yes | yes | yes | no |
| Delete report | yes | yes | no | no | no |
| Create/update site | yes | yes | no | no | no |
| Rebuild precursor patterns | yes | yes | yes | no | no |
| Read/decide normal analysis reviews | yes | yes | no | yes | no |
| Read/decide intervention reviews | yes | yes | no | yes | no |
| Read model metadata, performance, feedback | yes | yes | yes | no | no |

Use this matrix for route guards and hidden/disabled controls, but always
handle the backend's `403 INSUFFICIENT_ROLE`: the server is authoritative.
Both `GET /auth/me` and `GET /users/me` return the same `UserRead` shape.

## 4. Global response, error, and enum contract

Successful endpoint bodies are the resource shapes listed below, not wrapped in
a `{success: true}` envelope. Controlled errors have this shape:

```json
{
  "success": false,
  "error": {"code": "MACHINE_CODE", "message": "Safe user-facing message", "details": {}},
  "request_id": "uuid-or-null"
}
```

Validation errors are `422` with code `VALIDATION_ERROR`; `details` is an array
of Pydantic field errors. The response header `X-Request-ID` is returned for
normal responses; preserve it in client telemetry and show it in a support
view. The middleware also sends `X-Content-Type-Options: nosniff` and
`Referrer-Policy: strict-origin-when-cross-origin`.

| Status | Common codes | UI handling |
|---|---|---|
| 401 | `AUTHENTICATION_REQUIRED`, `INVALID_TOKEN`, `INVALID_CREDENTIALS` | Clear local token and navigate to sign-in. |
| 403 | `INSUFFICIENT_ROLE`, `INACTIVE_USER` | Keep current data if possible; show access denied. |
| 404 | `REPORT_NOT_FOUND`, `SITE_NOT_FOUND`, `REVIEW_NOT_FOUND`, `RULE_NOT_FOUND`, `INTERVENTION RECOMMENDATION_NOT_FOUND` | Show not-found state. Note the intervention code contains a space because it is derived from the entity label. |
| 409 | `EMAIL_ALREADY_REGISTERED`, `SITE_CODE_EXISTS`, `REPORT_ID_EXISTS`, `REVIEW_ALREADY_DECIDED`, `INTERVENTION_ALREADY_REVIEWED` | Refetch and explain the collision/final state. |
| 422 | `VALIDATION_ERROR`, `INVALID_REVIEW_DECISION`, `MODIFICATION_REQUIRED`, `INVALID_INTERVENTION_DECISION` | Bind field errors where possible; `MODIFY` requires correction/revised wording. |
| 503 | `DATABASE_UNAVAILABLE`, `DATABASE_ERROR`, `MODEL_UNAVAILABLE` | Retry affordance / service unavailable state. |
| 500 | `INTERNAL_ERROR` | Generic safe error with request ID. |

Enums sent by the UI are exact uppercase strings:

```text
UserRole: ADMIN | HSE_MANAGER | HSE_ANALYST | REVIEWER | VIEWER
ReportType: UNSAFE_ACT | UNSAFE_CONDITION | NEAR_MISS | INCIDENT
SourceType: PUBLIC | SYNTHETIC | USER_SUBMITTED | IMPORTED
ReportStatus: NEW | ANALYZED | REVIEW_REQUIRED | REVIEWED | CLOSED
SIFLevel: NON_SIF | LOW | MEDIUM | HIGH | REVIEW
BarrierStatus: EFFECTIVE | FAILED | MISSING | UNKNOWN
ReviewDecision: PENDING | APPROVE | REJECT | MODIFY
InterventionReviewStatus: PENDING | ACCEPTED | MODIFIED | REJECTED
```

## 5. Endpoint inventory (66 operations / 60 paths)

The following is the live OpenAPI inventory. All paths below are relative to
`/api/v1`.

| Area | Operations and primary query parameters |
|---|---|
| Authentication | `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `GET /users/me` |
| Deterministic analysis assistance | `POST /analyze`, `/analyze/counterfactual`, `/analyze/narrative`, `/analyze/interventions` |
| Corrective-action governance | `GET/POST /corrective-actions`, `/export`, `/{action_id}`, `/{action_id}/audit`, and state transitions `/start`, `/submit`, `/approve`, `/reject`, `/modify`, `/request-verification`, `/verify`, `/close`, `/cancel` |
| Health | `GET /health`, `/health/status`, `/health/ready` |
| Sites | `POST /sites`, `GET /sites`, `GET /sites/{site_id}`, `PATCH /sites/{site_id}` |
| Reports | `POST /reports`, `GET /reports`, `GET/PATCH/DELETE /reports/{report_id}`, `POST /reports/{report_id}/analyze` |
| Direct analysis | `POST /analyze` (does not persist a report) |
| Normal review queue | `GET /reviews?status=PENDING|REVIEWED|ALL&page=1&page_size=20`, `GET /reviews/{review_id}`, `POST /reviews/{review_id}/decision` |
| Intervention queue | `GET /interventions?report_id=<human-id>&priority=<string>`, `GET /interventions/summary`, `GET /interventions/{recommendation_id}`, `POST /interventions/{recommendation_id}/review` |
| Precursors | `GET /precursors` with `site,activity,hazard,barrier,priority,date_from,date_to,limit(1..200),sort(risk_score|recent)`; `GET /precursors/trends?limit`; `POST /precursors/rebuild`; `GET /precursors/{id}` and `/graph` |
| Risk | `GET /risk/sites`, `/activities`, `/hazards`, `/barriers`; each accepts `date_from,date_to,limit(1..200)` |
| Dashboard | `GET /dashboard/summary`, `/sif-trend?window=7d|30d|90d|1y`, `/lsr-distribution`, `/site-comparison`, `/activity-distribution`, `/hazard-distribution`, `/barrier-failures?window=…` |
| LSR knowledge | `GET /rules`, `GET /rules/{rule_id}`, `GET /rules/{rule_id}/analytics` |
| Model observability | `GET /models`, `/models/feedback`, `/models/performance`, `/models/{model_name}`, `/models/{model_name}/metrics` |

### Site requests

```ts
type SiteCreate = {
  name: string;                 // 1..255
  code: string;                 // 2..64, /^[A-Za-z0-9_-]+$/; stored uppercase
  location: string; region: string;
  description?: string | null; is_active?: boolean; // default true
};
type SiteUpdate = Partial<Omit<SiteCreate, "code">>;
type SiteRead = SiteCreate & {id: string; created_at: string; updated_at: string};
```

### Report requests and list response

```ts
type ReportCreate = {
  report_id?: string;           // 3..64; otherwise server creates SIF-YYYYMMDD-XXXXXXXX
  report_type: ReportType;
  report_text: string;          // meaningful trimmed content: default 10..20,000 chars
  site_id: string; location: string; department: string;
  activity?: string | null;
  reported_at: string; source_type: SourceType;
};
type ReportUpdate = {
  report_text?: string; location?: string; department?: string;
  activity?: string | null; status?: ReportStatus;
};
type ReportRead = ReportCreate & {
  id: string; report_id: string; status: ReportStatus; created_by: string;
  created_at: string; updated_at: string;
};
type ReportPage = {items: ReportRead[]; total: number; page: number; page_size: number};
```

`GET /reports` supports `page` (>=1), `page_size` (1..100), `site_id`,
`report_type`, `status`, `source_type`, `date_from`, `date_to`, and `search`
(max 200 chars). `report_id` in a report URL is the human-readable identifier,
not the UUID. A `POST /reports` only creates a `NEW` report; it does not analyse
it. `DELETE` succeeds with `{message:"Report deleted"}`.

### Deterministic analysis response

`POST /analyze` takes `{text: string}` and returns the same analysis shape with
`report_id` and `analysis_id` null. `POST /reports/{report_id}/analyze` persists
the result and returns populated IDs:

```ts
type RiskComponent = {name: string; score: number; reason: string};
type RiskDetail = {score: number; priority: string; components: RiskComponent[]; version: string};
type AnalysisResponse = {
  report_id: string | null; analysis_id: string | null;
  sif_potential: boolean; sif_level: SIFLevel; model_probability: number;
  activity: string | null; hazard: string | null; barrier: string | null;
  barrier_status: BarrierStatus; barrier_failure: string | null;
  life_saving_rule: string | null; rule_confidence: number;
  evidence_span: string | null; evidence_sentences: string[]; evidence_terms: string[];
  overall_confidence: number; review_required: boolean;
  model_version: string; explanation: string; risk: RiskDetail | null;
  reviewer_summary: string | null;
  llm_attempted: boolean; llm_used: boolean;
  llm_provider: string | null; llm_model_used: string | null;
  llm_timestamp: string | null; llm_error_code: string | null;
};
```

**UI treatment:** present the structured fields and `risk` as authoritative.
Show `reviewer_summary` under a visually separate “optional AI reviewer
assistance” label only when `llm_used === true`. When enabled but unavailable,
the deterministic analysis still succeeds and metadata records the controlled
failure (for example `TIMEOUT`, `PROVIDER_NOT_INITIALIZED`,
`INVALID_API_KEY`, `RATE_LIMITED`, `MALFORMED_OUTPUT`, or `INVALID_RESPONSE`).
Do not display an LLM error as a failure of the safety analysis.

### Normal analysis review queue

```ts
type ReviewQueueItem = {
  id: string; report_id: string; decision: ReviewDecision;
  reviewer_id: string | null; reviewed_at: string | null;
  report_text: string; evidence_span: string | null;
  overall_confidence: number | null; explanation: string | null;
  reviewer_comment: string | null;
  corrected_sif_level: SIFLevel | null; corrected_activity: string | null;
  corrected_hazard: string | null; corrected_barrier: string | null;
  corrected_barrier_status: BarrierStatus | null;
  corrected_barrier_failure: string | null;
  corrected_life_saving_rule: string | null;
};
type ReviewDecisionRequest = {
  decision: ReviewDecision; // submit APPROVE, REJECT, or MODIFY; never PENDING
  corrected_sif_level?: SIFLevel | null; corrected_activity?: string | null;
  corrected_hazard?: string | null; corrected_barrier?: string | null;
  corrected_barrier_status?: BarrierStatus | null;
  corrected_barrier_failure?: string | null;
  corrected_life_saving_rule?: string | null;
  reviewer_comment?: string | null;
};
type DecisionResponse = {
  review_id: string; decision: ReviewDecision; report_id: string;
  report_status: string; reviewer_id: string; reviewed_at: string; message: string;
};
```

`MODIFY` needs at least one non-null `corrected_*` field. Normal-review
corrections preserve the original `ReportAnalysis`; they are stored on `Review`.
The review is final after one decision; duplicate actions are `409`.

### Intervention recommendation queue

```ts
type InterventionRead = {
  id: string; report_id: string | null; precursor_pattern_id: string | null;
  intervention_rule_id: string; category: string; title: string;
  description: string; rationale: string; priority: string; action_type: string;
  review_required: boolean; evidence_snapshot: Record<string, unknown>;
  source_rule: string; engine_version: string; risk_priority: string | null;
  life_saving_rule: string | null; review_status: InterventionReviewStatus;
  reviewed_by: string | null; reviewed_at: string | null;
  reviewer_comments: string | null; reviewer_title: string | null;
  reviewer_description: string | null; reviewer_rationale: string | null;
  created_at: string;
};
type InterventionReviewRequest = {
  decision: InterventionReviewStatus; // ACCEPTED, MODIFIED, or REJECTED
  reviewer_comments?: string | null;
  reviewer_title?: string | null; reviewer_description?: string | null;
  reviewer_rationale?: string | null;
};
type InterventionSummary = {
  total: number; critical: number; pending: number; by_category: Record<string, number>;
};
```

This is a **separate** review workflow from `/reviews`. `MODIFIED` requires at
least one of `reviewer_title`, `reviewer_description`, or `reviewer_rationale`.
The deterministic original wording/evidence is retained; show reviewer changes
as an explicit overlay rather than replacing it. Recommendations are advisory,
not automated actions or work orders.

### Precursor, risk, dashboard, LSR, and model responses

```ts
type PrecursorSummary = {
  id: string; category: string; activity: string; hazard: string; barrier: string;
  failure_type: string; occurrence_count: number; sif_count: number;
  sif_density: number; recent_count: number; site_count: number;
  department_count: number; trend: string; risk_score: number; priority: string;
  first_seen: string | null; last_seen: string | null; why_it_matters: string;
};
type PrecursorDetail = PrecursorSummary & {
  sites: string[]; departments: string[];
  representative_reports: Array<{
    report_id: string; reported_at: string; site_name: string;
    department: string; sif_level: string | null;
  }>;
};
type PrecursorGraph = {
  nodes: Array<{id: string; label: string; type: string; statistics: Record<string, string|number>}>;
  edges: Array<{source: string; target: string; label: string}>;
};
type RiskItem = {
  name: string; report_count: number; sif_count: number; sif_density: number;
  barrier_failure_count: number; risk_score: number; risk_level: string; explanation: string;
};
type SiteRiskItem = RiskItem & {
  site_id: string; total_reports: number; sif_reports: number; sif_rate: number;
  high_risk_reports: number; active_precursor_patterns: number; recent_reports: number;
};
type BarrierRiskItem = {
  barrier: string; total_occurrences: number; failed_count: number; failure_rate: number;
  associated_sif_count: number; risk_score: number; risk_level: string; explanation: string;
};
type DashboardSummary = {
  total_reports: number; total_sif_reports: number; high_risk_reports: number;
  review_required: number; active_precursors: number; sites_monitored: number;
  sif_rate: number; high_risk_rate: number;
};
type TimeSeriesPoint = {
  date: string; total_reports: number; sif_reports: number; high_sif_reports: number; sif_rate: number;
};
type DistributionItem = {name: string; count: number; sif_count: number; sif_density: number; percentage: number};
type BarrierFailurePoint = {date: string; failed_count: number};
```

`/rules` and `/rules/{rule_id}` currently return the ORM-encoded life-saving
rule fields: `id`, `code`, `name`, `description`, `keywords`, `hazards`,
`barriers`, `is_active`, `created_at`, `updated_at`. A rule can be addressed by
UUID or code, such as `LSR-02`; rule analytics returns
`{life_saving_rule,total_reports,sif_reports,sif_density}`.

The models endpoints intentionally return JSON dictionaries rather than a
Pydantic response model. Render them as an analyst/admin observability surface,
not an operational safety decision. `GET /models/feedback` returns
`total_predictions`, `reviewed_predictions`, `approved_predictions`,
`corrected_predictions`, `correction_rate`, and `human_review_metrics`.
`/models/performance` returns `{offline_model_metrics,human_review_metrics}`.

## 6. Authoritative state and lifecycle rules

### Report lifecycle

```text
POST /reports -> NEW
PATCH /reports/{human-id} -> permitted only while NEW; request fields do not include status
POST /reports/{human-id}/analyze -> ANALYZED or REVIEW_REQUIRED (one analysis lifecycle per report)
  REVIEW_REQUIRED + POST /reviews/{id}/decision -> REVIEWED
```

One persisted analysis creates one `ReportAnalysis` and `ModelPrediction`.
Repeated analyse requests return `409 REPORT_ALREADY_ANALYZED`; a report must
not be edited after analysis because that would make its immutable evidence
snapshot stale. `PrecursorPattern` is an aggregate across current candidates;
it is a derived, rebuildable read model. A report may have no recurring pattern
yet, because the configured threshold is three occurrences.
`PrecursorPattern` is an aggregate across recurring candidates; it is a
derived, rebuildable read model. An analysed report may have no recurring
pattern yet, because the configured threshold is three occurrences.

### Source-of-truth matrix

| Data shown by UI | Authoritative source | Mutated by LLM? | User editable? |
|---|---|---:|---:|
| Submitted report | `Report` | no | create/update fields only |
| Activity/hazard/barrier/failure/evidence | deterministic NLP -> `ReportAnalysis` | no | only normal review correction fields, not the original analysis |
| SIF potential / level | deterministic classifier + rules -> `ReportAnalysis` | no | correction stored separately for normal review |
| LSR | deterministic mapper -> `ReportAnalysis` | no | correction stored separately for normal review |
| Risk score / priority/components | deterministic risk calculator -> `ReportAnalysis` | no | no API edit |
| Precursor candidate/pattern | deterministic NLP and aggregation | no | no API edit; rebuild only |
| `review_required` | deterministic confidence/routing | no | no API edit |
| Intervention original content | deterministic intervention engine | no | never overwritten; reviewer overlay stored separately |
| `reviewer_summary` | optional LLM provider | yes (only this assistive field) | no |

The frontend must not post a “corrected” normal-review value back into a
report or assume it updates the original analysis response. In the current
implementation, `corrected_*` values are exposed through the review history;
analytics and precursor aggregation query original/current deterministic
analysis and candidates. Make “model result” versus “human correction” explicit
in the UI.

## 7. Required frontend information architecture

Build these pages/features against the contract above, in order:

1. **Authentication and shell** — sign-up, sign-in, token-expiry handling,
   current-user lookup, role-aware navigation.
2. **Operational dashboard** — `DashboardSummary`, SIF trend, distributions,
   barrier failures, and links to filtered work queues. Empty states must be
   first-class; a fresh database legitimately returns zeros/empty arrays.
3. **Report intake and list** — validated report form, site selector, server
   error binding, database-backed filters/pagination, report status badges.
4. **Report analysis experience** — create then call persisted analyse; render
   source text, evidence, entities, SIF, LSR, barrier status, risk components,
   review-routing status, and assistant metadata. Direct `/analyze` can power a
   non-persistent “try analysis” tool, clearly labelled as not saved.
5. **Report detail limitation** — currently `GET /reports/{report_id}` returns
   only report fields, not analysis history. Retain the immediate analyse
   response in view state and use `/interventions?report_id=...` for related
   recommendations. Do not promise a reload-safe analysis-detail view until a
   backend read endpoint exists.
6. **Normal review queue** — reviewers can approve/reject/modify exactly once;
   use dynamic correction fields when `MODIFY` is selected; distinguish
   PENDING from completed review history.
7. **Intervention queue** — display source rule/evidence/rationale and separate
   original from human-modified wording; acceptance is a review decision, not
   an action-execution command.
8. **Precursor and risk intelligence** — ranking tables, filters, detail view,
   and graph rendered directly from the React-Flow-compatible node/edge data.
9. **Administration/observability** — sites for Admin/HSE Manager, precursor
   rebuild for analyst roles, LSR library, model metadata/feedback for analyst
   roles. Do not build user/role management: no API supports it.

For any mutation, disable the primary action while the request is in flight,
then invalidate/refetch its parent query and summaries. Because decisions are
one-way and may be taken by another reviewer, handle `409` by refetching rather
than attempting a blind retry.

## 8. Data model map for frontend developers

| Persisted concept | Relationships / frontend implication |
|---|---|
| `User` | Creates reports, makes normal/intervention decisions, may have audit logs. |
| `Site` | One site has many reports; site UUID is used in report creation and filters. |
| `Report` | Human ID is the API path key; UUID is the relational key. Has many analyses, predictions, reviews, and current precursor candidates. |
| `ReportAnalysis` | Immutable snapshot per analysis run, including deterministic results/risk plus optional LLM metadata. No analysis-read endpoint currently exists. |
| `ModelPrediction` | One persistent prediction per analysis; internal/audit/feedback source, not exposed per report. |
| `Review` | Normal analysis review; holds final decision and any `corrected_*` overlay. |
| `PrecursorCandidate` | Current deterministic per-report signal; no direct endpoint. |
| `PrecursorPattern` | Recurring aggregate exposed by precursor endpoints and can create a preventive intervention. |
| `InterventionRecommendation` | Deterministic advisory result for a report or a precursor pattern, with separate reviewer overlay/final decision. |
| `LifeSavingRule` | Seeded reference data exposed by `/rules`. |
| `AuditLog` | Written for report mutation/analysis and both review flows, but not exposed through an API. |

## 9. Security, quality, and API-gap audit

### Confirmed safeguards

- Passwords are Argon2-hashed; password hashes are not returned.
- JWT bearer decoding loads an active user on each request; role checks are
  server-side.
- Report text has one shared boundary validator for direct and persisted
  analysis (default meaningful length 10–20,000 chars).
- Controlled errors avoid raw SQL/provider diagnostics, and request IDs make
  support correlation possible.
- LLM calls are optional, bounded, use provider-specific prompt instruction
  separation, validate structured output, and return controlled failures.
- Phase-J authority tests cover adverse LLM output and verify deterministic
  SIF/LSR/barrier/precursor/risk/review results are unchanged.
- Review and intervention finalization use database row locks where supported;
  repeated finalization returns `409`.

### Gaps to design around (not changed by this audit)

| Priority | Finding | Frontend consequence / recommended backend follow-up |
|---|---|---|
| High | No authenticated read API for a report's analyses, risk, LLM metadata, predictions, candidates, or audit trail. | A refreshed report-detail page cannot reconstruct its analysis result from documented REST endpoints. Add a read-only report-detail aggregate/analysis-history endpoint before claiming full reload-safe detail. |
| High | Audit events are durable but no audit-log API exists. | Do not build an audit timeline as if it is available. Add a role-gated, paginated read endpoint if required for release/audit UX. |
| High | Registration produces only `VIEWER`; no role administration/invitation path exists. | Provision author/reviewer roles outside the UI, or add a protected user-admin API before role onboarding is a frontend requirement. |
| Resolved | `PATCH /reports` formerly accepted arbitrary `ReportStatus` values for report writers. | Lifecycle status is no longer a request field; PATCH is limited to `NEW` reports and later edits return `409 REPORT_NOT_EDITABLE`. |
| Medium | Review list drops its total despite accepting pagination; interventions have no pagination/status/category filter. | Avoid misleading page-count UI and plan backend pagination/filter additions as data volume grows. |
| Medium | `/models` and `/rules` have untyped/dynamic route response declarations. | Generate core client types from OpenAPI for typed endpoints, but manually validate these two surfaces or add response schemas server-side. |
| Medium | No refresh/logout/revocation API and no explicit rate limiting shown in the application code. | Implement client expiry handling; do not imply server-side logout or abuse protection. Treat rate limiting as a deployment/API-gateway concern until implemented. |
| Resolved | API OpenAPI title and description were stale. | The generated API now identifies SIF Sentinel and describes deterministic safety intelligence and human review. |
| Low | No upload endpoint, realtime events, saved dashboard filters, notifications, user profile edits, or export endpoints. | Do not scaffold UI flows that require these behaviors without a backend feature request. |

## 10. Demo data and safe product claims

`scripts/demo/seed_demo_data.py` seeds synthetic sites, demonstration users,
LSR data, reports, analyses, precursors, and interventions. Its credentials are
explicitly demo-only and must not be copied into client code or a production
deployment. The training/documentation materials label the bundled model data
as synthetic; the UI must not claim validated real-world predictive accuracy,
automatic incident prevention, or that an intervention has been executed.

Recommended UI language is “risk signal”, “deterministic recommendation”,
“requires human review”, and “consider/verify”. Never render an LLM summary as
a fact, medical/safety instruction, or replacement for an HSE decision.

## 11. Verification performed for this handoff

- Inspected FastAPI router, dependencies, middleware, schemas, ORM models,
  services, configuration, migrations/repository layout, tests, OpenAPI, and
  the frontend placeholder.
- Generated the current OpenAPI inventory: **66 operations across 60 paths**.
- Executed `pytest tests/` against the current SQLite test configuration in a
  background terminal capture (needed only to avoid the desktop console's
  30-second streaming window): **158 passed, 5 warnings, 56.50 s**. The
  warnings are third-party/runtime deprecations from FastAPI/Starlette
  TestClient, the Windows selector event-loop policy, and `google-genai` type
  aliases; there were no test failures or errors.

## 12. Frontend release readiness

**Frontend planning readiness: 8/10.** The operational read/write APIs, RBAC,
error format, analysis contract, dashboard metrics, precursor graph, and two
review workflows are sufficiently concrete to begin UI implementation now.
The score is not 10/10 because reload-safe analysis detail, audit visibility,
role onboarding, and scalable queue pagination are API gaps, not frontend
problems. Build the listed pages with explicit empty/loading/error states and
raise those four items as backend follow-ups rather than inventing client-side
sources of truth.

**BACKEND AUDIT COMPLETE — READY FOR FRONTEND PHASE PLANNING**

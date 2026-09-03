# SIF Sentinel demo claims

All scenarios and seed data used in the demo are **SYNTHETIC DEMO DATA**.

| Claim | Evidence | Where implemented | Limitation |
| --- | --- | --- | --- |
| Produces structured safety evidence and SIF/LSR results | Deterministic NLP pipeline and persisted analysis fields | `app/services/nlp/`, `app/services/analysis/analysis_service.py` | Prototype model/evidence rules are not a measure of real-world predictive performance. |
| Identifies recurring safety precursors | Normalized candidate aggregation with recurrence and trend logic | `app/services/precursor_engine/` | A pattern needs sufficient stored observations; it is not a prediction of an accident. |
| Ranks deterministic safety risk | Transparent component-based score and priority mapping | `app/services/risk_engine/` | Risk is decision-support context, not a probability or regulatory conclusion. |
| Provides evidence-backed intervention recommendations | Deterministic control-state, LSR, and precursor mappings | `app/services/intervention_service.py` | Recommendations are advisory; they do not execute actions or replace HSE judgment. |
| Preserves human review and auditability | Review state machines and audit records | `app/services/review_service.py`, `app/services/audit_service.py` | Reviewers remain responsible for final decisions. |
| Optional LLM reviewer summaries cannot change safety decisions | LLM assistance receives authoritative context but writes only assistance metadata/summary | `app/services/llm/`, `app/services/analysis/analysis_service.py` | A real provider demonstration requires a configured valid provider key; disabled mode is the baseline demo. |

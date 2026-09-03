# Intervention Intelligence

## Purpose and authority

Phase K converts existing structured evidence, SIF/LSR results, barrier state,
precursor patterns, and Phase I risk priority into deterministic, advisory
recommendations. **Intervention recommendations are advisory decision support.
They do not automatically execute safety actions and do not replace HSE
professional judgment.**

The authority chain is report → structured evidence → SIF/LSR → precursor →
risk → intervention recommendation → HSE review → audit. The engine never
changes SIF, LSR, risk, audit history, or a corrective-action workflow.

## Taxonomy and hierarchy

The normalized categories are control restore/strengthen, barrier restore or
verification, isolation/permit verification, engineering control, supervisory
verification, field inspection, monitoring, and escalation. Machine guarding
maps to `ENGINEERING_CONTROL` before PPE because engineering controls are
stronger. The engine does not assign a hierarchy when evidence does not name a
relevant barrier.

## Deterministic rules

`MISSING` maps to `CONTROL_RESTORE`; `NOT_VERIFIED` and `UNKNOWN` map to
verification; `FAILED` maps to `BARRIER_RESTORE`; `BYPASSED` maps to immediate
human review plus control restoration; `INEFFECTIVE` maps to strengthening.
Verified/effective controls generate no corrective recommendation. Priority is
derived transparently from Phase I risk and control state, not from a probability.
Critical risk or bypassing is critical; high risk or degraded controls are high;
recurrence or medium risk is medium; otherwise low.

LSR increases specificity only when a weakness exists: Energy Isolation plus
unverified isolation maps to `ISOLATION_VERIFY`; Permit-related weakness maps
to `PERMIT_VERIFY`. Recurrent precursor patterns with at least three
observations create one idempotent preventive/supervisory recommendation;
increasing trends use escalation wording. The language intentionally says
"recommended to address" rather than claiming accident prevention.

## Worked examples

1. Maintenance + energy isolation not verified → verify energy isolation,
   verification action, with evidence and LSR recorded.
2. Work at height + failed fall protection → restore failed barrier,
   corrective action.
3. Machine operation + guarding missing → restore effective machine guarding,
   engineering-control recommendation.
4. Permit-related activity + unknown authorization → verify permit,
   verification action rather than assuming failure.
5. Four increasing control-unverified precursor observations → targeted
   supervisory verification and escalation recommendation.

## Persistence, review, and security

Each recommendation stores an immutable original title, description, rationale,
evidence snapshot, source rule, engine version (`v1`), priority, action type,
review-required state, and timestamp. The idempotency key is report/pattern +
rule + engine version.
HSE reviewers can accept, reject, or modify wording only; reviewer wording is
stored separately so the original remains auditable. Priority, evidence,
version, and rule cannot be supplied by an API caller. Review actions are RBAC
restricted and audited.

## LLM boundary and limitations

No LLM produces or changes authoritative intervention recommendations. Optional
LLM wording assistance is intentionally not wired into Phase K; deterministic
recommendations remain available when an LLM is disabled, fails, or hallucinates.
The engine sends no email, SMS, stop-work order, disciplinary action, regulator
notice, or external request. It does not claim effectiveness percentages,
prevented incidents, causal outcomes, or regulatory conclusions.

## API and tests

`GET /api/v1/interventions`, `/summary`, and `/{id}` expose the advisory queue;
`POST /{id}/review` records HSE review. Tests cover taxonomy, state mappings,
LSR specificity, pattern recommendations, priority/action type, evidence,
idempotency, original-preserving modification, and rejection on SQLite and
PostgreSQL through the shared suite.

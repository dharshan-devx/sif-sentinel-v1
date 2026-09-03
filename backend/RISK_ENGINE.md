# Phase I: Deterministic Safety Risk Engine

## Philosophy
The Safety Risk Engine in SIF Sentinel evaluates incoming safety reports to assign a deterministic risk score and priority. It acts as **decision support**, ensuring high-risk incidents surface reliably without fabricating probabilities.

## Core Tenets
1. **Explainable and Deterministic**: The risk score is built via additive, traceable components.
2. **Conservative Defaults**: Ambiguous or missing data errs on the side of safety (e.g. "unknown" barrier verification contributes to risk).
3. **Evidence-Based**: Risk isn't derived from a black-box model but from the structured NLP evidence (`StructuredEvidence`), combined with historical precursor tracking.

## Risk Calculation

The risk engine generates a score from `0` to `100`, which maps to priority levels: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
Scores are the sum of the following four components:

### 1. Consequence Potential (Max 30 points)
Derived from the classification model's SIF-level output.
- `HIGH` SIF Level: **+30 points**
- `MEDIUM` SIF Level: **+20 points**
- `LOW` SIF Level: **+10 points**
- Base SIF Potential (without a specific level): **+15 points**

### 2. Control Degradation (Max 30 points)
Derived from the `verification_status` of identified barriers in the report.
- `failed`, `bypassed`, `not performed`: **+30 points** (Critical degradation)
- `ineffective`: **+20 points**
- `not verified`: **+15 points**
- `unknown`: **+10 points** (Ambiguity introduces risk)
- `verified`: **+0 points**

### 3. Life-Saving Rule (LSR) Relevance (Max 15 points)
Derived from the mapping of the incident to controlled Life-Saving Rules.
- Incident maps to an LSR: **+15 points**

### 4. Precursor Recurrence (Max 25 points)
Integrates with the Phase H Precursor Engine. If the incoming incident matches a tracked precursor pattern:
- Precursor Priority `CRITICAL`: **+25 points**
- Precursor Priority `HIGH`: **+20 points**
- Precursor Priority `MEDIUM`: **+10 points**
- Precursor Priority `LOW`: **+5 points**

## Thresholds (Defined in `config.py`)
- `CRITICAL`: >= 80 points
- `HIGH`: >= 60 points
- `MEDIUM`: >= 30 points
- `LOW`: < 30 points

## Configuration Management
Risk calculation weights and boundaries are centralized in `app/core/config.py`. The schema includes a `risk_version` (e.g. `1.0.0`) attached to every analysis to ensure auditability of risk algorithms over time.

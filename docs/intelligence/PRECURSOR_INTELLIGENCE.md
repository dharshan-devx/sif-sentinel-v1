# Phase H: Precursor Intelligence Hardening

## Overview
As part of Phase H, the SIF SENTINEL platform's Precursor Intelligence engine was hardened to provide a defensible, threshold-based aggregation of leading safety signals. This layer identifies repeated weak signals, unsafe patterns, and control degradations that may precede Serious Injury or Fatality (SIF) events.

## Key Concepts

### 1. Precursor Candidates
Instead of immediately treating any single unsafe observation as a "precursor," the system now parses raw safety reports into `PrecursorCandidate` records. These candidates are mapped to recognized precursor categories (e.g., `CONTROL_MISSING`, `LSR_VIOLATION`, `HAZARD_REPEATED`) using a taxonomy rules engine (`app/services/nlp/precursor_rules.py`).

### 2. Configurable Thresholds
A precursor is defined by repetition. The `PatternAggregator` now enforces configurable thresholds before surfacing a pattern as a formal Precursor:
- **`PRECURSOR_MIN_OCCURRENCES`**: The minimum number of identical candidates required to trigger a precursor alert (Default: 3).
- **`PRECURSOR_LOOKBACK_DAYS`**: The rolling time window evaluated for these occurrences (Default: 90 days).

### 3. Priority Scoring
To clarify the severity of a precursor signal without making false statistical claims, the previous numeric `risk_level` has been replaced with a categorical `priority` field:
- **CRITICAL**
- **HIGH**
- **MEDIUM**
- **LOW**

Priority is derived from a composite score that considers SIF density, barrier failure rates, recency, trend (e.g., Increasing, New, Decreasing), and geographic spread.

## Architecture & Data Flow

1. **Analysis Pipeline**: The `AnalysisService` processes incoming unstructured safety reports. It invokes the `PrecursorRulesEngine` to extract structured evidence and generate `PrecursorCandidate` entries, which are persisted alongside the `ReportAnalysis`.
2. **Aggregation**: The `PatternAggregator` periodically groups candidates by `[category, activity, hazard, barrier, failure_type]`. It applies the lookback window and occurrence thresholds to filter noise.
3. **Trend & Priority**: For patterns meeting the threshold, the aggregator calculates metrics like SIF density, trend, and overall risk score, which determines the final `priority`.
4. **Service Exposure**: The `PrecursorService` surfaces these established patterns through the API, allowing users to filter by category, priority, and site, and offering full traceability back to the original representative reports.

## Defensibility & Principles
- **No Fabrication**: The system does not fabricate trends or predict specific incidents. It strictly aggregates observed leading indicators.
- **Decision Support**: It operates as a decision-support tool, surfacing "weak signals" that require human investigation and intervention before an incident occurs.
- **Traceability**: Every surfaced precursor pattern can be traced directly back to the specific unstructured reports that contributed to it.

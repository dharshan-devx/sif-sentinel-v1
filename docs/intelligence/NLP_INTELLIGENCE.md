# NLP Intelligence Hardening (Phase G)

## Overview
Phase G upgrades the NLP layer from a flat keyword-matching system to a structured, sentence-aware evidence engine. It introduces `StructuredEvidence` representations of safety concepts with native support for negation, temporal context, and control verification status.

## Key Upgrades

### 1. Structured Evidence Model
The `EvidenceItem` dataclass now tracks metadata for every extracted concept:
- `normalized_concept`: The standardized term (e.g., "Energy Isolation").
- `original_span`: The raw text fragment.
- `negated`: Whether the concept was explicitly negated (e.g., "no", "not", "without").
- `verification_status`: The resolved status of a control (e.g., `verified`, `not verified`, `missing`, `failed`, `unknown`).
- `temporal_status`: Contextual modifiers like `before`, `during`, or `planned`.

### 2. Context-Aware Extraction
The `entity_extractor.py` no longer evaluates document-level substrings. It extracts concepts sentence-by-sentence and evaluates the immediate adjacent text (up to a 5-word window) to detect modifiers:
- **Negation:** "not verified", "without isolation".
- **Verification:** "was verified", "checked".
- **Temporal/Contextual:** "before maintenance", "planned isolation".

A specialized temporal distance check ensures that terms like "before" are accurately bound. For instance, "Before maintenance, isolation was verified" does not incorrectly negate the verification, whereas "started work before isolation was verified" correctly marks the control as `not verified`.

### 3. Intelligent Life-Saving Rule Mapping
The `lsr_mapper.py` now leverages the structured evidence to avoid false positives. An incident will only strongly map to a Life-Saving Rule violation if a control was explicitly found to be missing, bypassed, or unverified. If a control was properly applied and verified, the LSR mapper will gracefully de-prioritize the rule violation.

### 4. Procedural Explanations
The `analysis_pipeline.py` explanation generator was overhauled to construct semantic, human-readable explanations directly from the extracted `EvidenceItem` objects.
Example output:
> "Evidence identified Maintenance, Stored Energy. The report states that Energy Isolation was NOT verified. This evidence maps to the Energy Isolation Life-Saving Rule. The ML model identified 'shock', 'maintenance' as top predictive terms. Human review is recommended to confirm this assessment."

### 5. Automated Ambiguity Detection
If a safety control is mentioned but its verification status cannot be determined (e.g., "The lockout procedure was discussed prior to maintenance"), the system automatically routes the report for manual human review, explicitly citing the ambiguous verification state in the explanation.

## Test Coverage
Verified by `tests/test_nlp_evidence.py` ensuring that:
- Verified controls do not trigger failure mappings.
- Unverified/Missing controls correctly trigger failures.
- Ambiguous controls correctly trigger review requirements.
- Full system backward compatibility is maintained on both SQLite and PostgreSQL.

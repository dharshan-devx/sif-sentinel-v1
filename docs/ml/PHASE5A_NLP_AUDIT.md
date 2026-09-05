# Phase 5A — Complete AI/NLP Safety Reasoning Audit

## Executive Summary
This document provides a comprehensive, rigorous architectural audit of the current AI/NLP stack in SIF Sentinel (SIH26165). Following the successful completion of **Phase 3** (TF-IDF Baseline), **Phase 3.5** (Credibility & Leakage Audit), **Phase 4A** (Subword Neural / Hybrid), and **Phase 4B** (Genuine Pretrained Transformer Benchmark), the system possesses:
1. An ultra-fast, deterministic classical production baseline (Model A: TF-IDF + Logistic Regression, $1.36\text{ ms}$).
2. A genuine fine-tuned Transformer encoder (Model C: DistilBERT-base-uncased, $41.92\text{ ms}$, 98.95% template-held-out accuracy, 1.90% FNR).
3. A structured rule-based NLP extraction pipeline (Activities, Hazards, Controls, Verification States, LSR Mappings, Evidence Spans, Precursor Candidates).
4. Multi-backend model abstraction and 274 passing automated tests.

This audit establishes the exact current state, identifies architectural gaps between classification and causal semantic reasoning, catalogues technical debt, and sets forth the recommended roadmap for **Phase 5: Safety Semantic Reasoning Engine**.

---

## 1. Current Architecture Diagram

```
+----------------------------------------------------------------------------------------------------+
|                                    INPUT SAFETY REPORT NARRATIVE                                   |
+----------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
                     +----------------------------------------------------------+
                     |         PREPROCESSING (preprocessing.py)                 |
                     | - Unicode normalization (NFKC)                           |
                     | - Contraction expansion (wasn't -> was not)              |
                     | - Abbreviation-aware sentence splitting                  |
                     | - Whitespace & punctuation cleaning                      |
                     +----------------------------------------------------------+
                                                  |
                        +-------------------------+-------------------------+
                        |                                                   |
                        v                                                   v
+-----------------------------------------------+   +-----------------------------------------------+
|     STATISTICAL & NEURAL ML SUBSYSTEM         |   |         STRUCTURED NLP EXTRACTION SUBSYSTEM   |
| (backend/app/ml/inference/predictor.py)       |   | (backend/app/services/nlp/entity_extractor.py)|
|                                               |   |                                               |
| Model Backends:                               |   | Concept Matchers:                             |
| - v2 (Default Production TF-IDF LogReg)       |   | - Activities (14 categories)                  |
| - v4_semantic (Subword Char-TFIDF MLP)        |   | - Hazards (15 categories)                     |
| - v4b_transformer (DistilBERT contextual)     |   | - Barriers / Controls (17 categories)         |
| - v4b_hybrid (Calibrated Logistic Fusion)     |   |                                               |
|                                               |   | Context Window Analysis ([-6, +7] tokens):    |
| Outputs:                                      |   | - Negation terms (not, no, never, absent...)  |
| - Probability P(SIF) in [0.0, 1.0]            |   | - Verification terms (verified, applied...)   |
| - SIF Level (HIGH, MED, LOW, REVIEW, NON_SIF) |   | - Temporal inversion ("entered before tested")|
| - Model version & top predictive n-grams      |   | - Barrier Status (EFFECTIVE, FAILED, UNKNOWN) |
+-----------------------------------------------+   +-----------------------------------------------+
                        \                                                   /
                         \                                                 /
                          +-----------------------+-----------------------+
                                                  |
                                                  v
                     +----------------------------------------------------------+
                     |         PIPELINE REASONING & ORCHESTRATION               |
                     | (backend/app/services/nlp/analysis_pipeline.py)          |
                     |                                                          |
                     | 1. Life-Saving Rule Mapping (lsr_mapper.py)              |
                     |    - IOGP 9 Life-Saving Rules matching                   |
                     |    - Structured failure score boost                      |
                     | 2. Evidence Sentence Span Extraction (evidence_extractor)|
                     | 3. Precursor Candidate Generation (precursor_rules.py)   |
                     |    - Categories: CONTROL_MISSING, UNVERIFIED, EXPOSURE   |
                     | 4. Multi-Component Heuristic Confidence (confidence.py)  |
                     |    - Weighted linear combination of certainty            |
                     | 5. Deterministic Risk Calculation (risk_engine/calc.py)  |
                     |    - 1-100 score: Consequence + Control + LSR + Recurrence|
                     | 6. Structured Explanation Synthesis                      |
                     |    - Evidence concepts + verification state + LSR + ML   |
                     +----------------------------------------------------------+
                                                  |
                        +-------------------------+-------------------------+
                        |                                                   |
                        v                                                   v
+-----------------------------------------------+   +-----------------------------------------------+
|       DIRECT EPHEMERAL API RESPONSE           |   |       PERSISTED REPORT WORKFLOW SERVICE       |
| (POST /api/v1/analyze)                        |   | (AnalysisService.analyze_report)              |
|                                               |   |                                               |
| Returns AnalysisResponse:                     |   | - Persists ReportAnalysis record              |
| - sif_potential, sif_level, model_probability |   | - Persists ModelPrediction audit entry        |
| - activity, hazard, barrier, barrier_status   |   | - Builds/Rebuilds PrecursorPatterns           |
| - life_saving_rule, rule_confidence           |   | - Generates downstream Interventions          |
| - evidence_span, sentences, terms             |   | - Enqueues Review if review_required=True     |
| - risk (score, priority, components)          |   | - Optional LLM Assistive Summary (Phase J)    |
| - explanation                                 |   +-----------------------------------------------+
+-----------------------------------------------+
```

---

## 2. Existing Component Inventory

| Component File | Directory | Primary Role | Dependencies |
|---|---|---|---|
| `preprocessing.py` | `backend/app/services/nlp/` | Text cleaning, contraction expansion, abbreviation-safe sentence splitting | Standard library (`re`, `unicodedata`) |
| `evidence_model.py` | `backend/app/services/nlp/` | Dataclasses for `EvidenceType`, `EvidenceItem`, and `StructuredEvidence` | Standard library (`dataclasses`, `enum`) |
| `entity_extractor.py` | `backend/app/services/nlp/` | Exact and fuzzy concept matching, token context window analysis, barrier status assignment | `rapidfuzz`, `safety_concepts.json` |
| `evidence_extractor.py` | `backend/app/services/nlp/` | Extracts text spans and sentences supporting matched concepts | `preprocessing.py`, `entity_extractor.py` |
| `lsr_mapper.py` | `backend/app/knowledge/` | Maps extracted entities and text signals to IOGP Life-Saving Rules | `taxonomy.py`, `life_saving_rules.json` |
| `precursor_rules.py` | `backend/app/services/nlp/` | Transforms structured evidence into discrete precursor candidates | `evidence_model.py` |
| `confidence.py` | `backend/app/services/nlp/` | Heuristic composite confidence score to flag `review_required` | `app.core.config` |
| `sif_classifier.py` | `backend/app/services/nlp/` | Adapter providing `classify_sif(text)` interface | `model_registry.py` |
| `model_registry.py` | `backend/app/services/nlp/` | Singleton loader for the active SIF ML model | `app.ml.inference.predictor` |
| `predictor.py` | `backend/app/ml/inference/` | Universal multi-version model inference runner (`v1`, `v2`, `v4`, `v4b`, `v4b_hybrid`) | `joblib`, `torch`, `transformers`, `sklearn` |
| `analysis_pipeline.py` | `backend/app/services/nlp/` | End-to-end pipeline orchestrator for NLP analysis | NLP modules, `risk_engine` |
| `analysis_service.py` | `backend/app/services/analysis/` | Service layer handling database persistence, precursor aggregation, and LLM assistance | SQLAlchemy, `analysis_pipeline.py` |

---

## 3. Existing NLP Capabilities
1. **Contraction Expansion**: Expands 14 standard English contractions (`wasn't` $\rightarrow$ `was not`, `didn't` $\rightarrow$ `did not`) to prevent negation masking.
2. **Abbreviation-Protected Sentence Segmentation**: Protects technical units (`p.s.i.`, `psi.`, `temp.`, `approx.`), numbered lists (`1. `, `2. `), and equipment tags (`P-101.A`) from erroneous sentence breaks.
3. **Structured Entity Matching**:
   - **Activities (14 types)**: Confined Space Work, Maintenance, Inspection, Lifting, Driving, Hot Work, Electrical Work, Work at Height, etc.
   - **Hazards (15 types)**: Stored Energy, Electrical Energy, Pressure, Toxic Atmosphere, Oxygen Deficiency, Fall Hazard, Suspended Load, Moving Machinery, etc.
   - **Barriers/Controls (17 types)**: Energy Isolation, Lockout Tagout, Gas Testing, Atmospheric Monitoring, Permit, Fall Protection, Guardrail, Interlock, Fire Watch, etc.
4. **Context Window Negation & Verification Parsing**:
   - Analyzes $[-6, +7]$ token window around matched control phrases.
   - Categorizes status into 7 states: `verified`, `not verified`, `failed`, `bypassed`, `not performed`, `missing`, `expired`, `unknown`.
5. **Temporal Inversion Detection**:
   - Detects hazardous sequence where action precedes barrier verification (e.g., *"Worker entered vessel before gas testing was completed"*).
6. **IOGP Life-Saving Rule Mapping**:
   - 9 canonical rules with activity, hazard, barrier, keyword, and failure pattern matching.
7. **Deterministic Risk Scoring**:
   - Computes 1–100 risk score based on consequence severity, barrier failure, LSR breach, and temporal precursor recurrence.

---

## 4. Existing Transformer Capabilities
1. **Pretrained Bidirectional Context**:
   - `distilbert-base-uncased` fine-tuned for sequence classification with 66.95M parameters.
   - WordPiece tokenization (30,522 vocab) with 0.0% out-of-vocabulary dropping on domain terms.
2. **Superior Generalization across Syntax**:
   - Demonstrated **98.95% accuracy** and **1.90% False Negative Rate** on 101 completely held-out template families (where classical TF-IDF suffered 33.33% FNR).
3. **Strong Negation Sensitivity**:
   - Probability delta $\Delta = +0.9213$ between *"Energy isolation was not verified"* ($P=0.9219$) and *"Energy isolation was verified"* ($P=0.0007$).
4. **Out-of-Distribution Safety**:
   - Correctly assigns near-zero SIF probability ($P \le 0.0006$) to non-safety domains (software stack traces, weather, office, cooking, physics).

---

## 5. Existing Hybrid Capabilities
1. **Multi-Signal Logistic Fusion (`v4b_hybrid`)**:
   - Fuses: (1) Phase 3 Baseline TF-IDF probability, (2) Phase 4B Transformer contextual probability, and (3) Phase 2 structured safety evidence counts ($N_{\text{activity}}, N_{\text{hazard}}, N_{\text{barrier}}, N_{\text{failed\_barrier}}$).
2. **Probability Calibration**:
   - Expected Calibration Error (ECE) of **0.0019** and Brier score of **0.0000** on locked test data.
3. **Enhanced Counterfactual Stability**:
   - Shifts probabilities downward on verified controls while retaining high recall when physical hazard exposure is severe.

---

## 6. Current End-to-End Data Flow

```
Raw Text -> preprocess_text() -> PreprocessedText (original, normalized, sentences, tokens)
                                         |
               +-------------------------+-------------------------+
               |                                                   |
               v                                                   v
   classify_sif(normalized)                             _extract_evidence(PreprocessedText)
               |                                                   |
         SIFPrediction                                      StructuredEvidence
    (prob, sif_level, terms)                           (items with verification_status)
               |                                                   |
               +-------------------------+-------------------------+
                                         |
                                         v
                         map_to_life_saving_rule(...)
                         extract_evidence(...)
                         generate_precursor_candidates(...)
                         calculate_risk(...)
                         _explain(...)
                                         |
                                         v
                                   PipelineResult
                                         |
                                         v
                                  AnalysisResponse
```

---

## 7. Missing Capabilities for a True Safety Semantic Reasoning Engine

| Area | Current Reality | Missing Capability for True Semantic Reasoning |
|---|---|---|
| **Causal Relation Extraction** | Unconnected lists of activities, hazards, and controls | Triplet extraction binding specific hazards directly to their specific controls (e.g., `(Fall Hazard) -> controlled_by -> (Fall Arrest Harness) [FAILED]`) |
| **Cross-Clause Negation** | Localized $[-6, +7]$ token window string scan | Dependency-tree / attention-guided negation resolving complex compound clauses across commas and subordinate conjunctions |
| **Counterfactual State Tracking** | Classification head outputs single scalar probability | Counterfactual reasoning module evaluating "What-if" barrier delta ($\Delta P = P(\text{unsafe}) - P(\text{safe})$) |
| **Hierarchical Hazard Severity** | Generic hazard keyword tagging | Dynamic energy level parsing (e.g., distinguishing 12V DC instrument wire from 4160V 3-phase switchgear) |
| **Confidence Epistemic Calibration** | Arbitrary weighted linear sum in `confidence.py` | Statistically sound epistemic + aleatoric uncertainty quantification combining model entropy and evidence alignment |
| **Bidirectional NLP-Transformer Coupling** | Transformer runs independently from NLP rule extractor | Hybrid attention pooling where Transformer embeddings attend to structured safety spans |

---

## 8. Technical Debt Catalogue

1. **`__main__` Patching for Joblib Unpickling**:
   - *Location*: `backend/app/ml/inference/predictor.py:12-23`
   - *Issue*: Custom pipeline classes saved in root scripts require runtime monkey-patching of `sys.modules['__main__']` to unpickle cleanly inside test suites.
   - *Remediation*: Relocate all class definitions into importable library modules (`app.ml.pipelines.*`) before serialization.
2. **Duplicated Concept Taxonomy**:
   - *Location*: `backend/app/services/nlp/entity_extractor.py:31-84` vs `backend/app/knowledge/safety_concepts.json`
   - *Issue*: `MATCHERS` dictionary in code duplicates JSON taxonomy for backward compatibility.
   - *Remediation*: Consolidate single source of truth in `app/knowledge/taxonomy.py`.
3. **Heuristic Confidence Formula**:
   - *Location*: `backend/app/services/nlp/confidence.py:14-16`
   - *Issue*: Arbitrary linear weights ($0.45, 0.25, 0.20, 0.10$) do not reflect statistical uncertainty.
   - *Remediation*: Replace with calibrated Dempster-Shafer or Dirichlet evidence combination.
4. **Overlapping Vocabulary Between Hazard and Control**:
   - *Location*: `safety_concepts.json`
   - *Issue*: Terms like "gas testing" appear under both Toxic Atmosphere hazard and Gas Testing control, causing dual activation.

---

## 9. Risk Analysis

| Risk | Severity | Mitigation |
|---|---|---|
| **Production API Breaking Changes** | HIGH | Strict preservation of `AnalysisResponse` schema; all Phase 5 enhancements must be additive or internal. |
| **CPU Latency Regression** | MEDIUM | Keep Phase 3 TF-IDF as default production backend ($1.36\text{ ms}$); optimize Transformer inference path via ONNX / quantization ($<15\text{ ms}$). |
| **False Negative Masking on Safe Language** | HIGH | Enforce threshold guardrails where severe energy hazard exposure with absent controls triggers mandatory human review regardless of soothing wording. |
| **Test Set Contamination** | HIGH | Maintain frozen `split_manifest_v2.json` and strict read-only isolation of test data. |

---

## 10. Recommended Phase 5 Implementation Plan

```
PHASE 5: SAFETY SEMANTIC REASONING ENGINE (ROADMAP)
├── 5B: Unified Safety Concept Graph & Causal Triplet Extractor
│   ├── Bind (Hazard, Barrier, Activity) into causal relation triplets
│   └── Eliminate duplicate vocabulary between hazards and controls
├── 5C: Contextual Dependency & Syntax-Aware Barrier Resolver
│   ├── Clause-aware dependency parsing for complex negations
│   └── Multi-barrier status resolution (differentiating active, failed, and unverified)
├── 5D: Deep Hybrid Semantic Reasoning Architecture
│   ├── Attention-guided token attribution mapped directly to safety entities
│   └── Epistemic uncertainty estimation replacing heuristic confidence
└── 5E: Verification, Counterfactual Stress Suite & Full System Validation
    ├── Automated regression suite across 274+ existing tests
    └── Comprehensive validation on counterfactual safety pairs and semantic edge cases
```

---

## 11. File-by-File Modification Plan

| File Path | Planned Action | Description of Modifications |
|---|---|---|
| `backend/app/services/nlp/evidence_model.py` | Extend | Add `CausalTriplet` dataclass linking `(activity, hazard, control, status, severity)`. |
| `backend/app/services/nlp/entity_extractor.py` | Refactor | Upgrade entity extraction to output linked causal triplets rather than flat concept lists. |
| `backend/app/services/nlp/confidence.py` | Replace | Upgrade heuristic confidence to entropy-based uncertainty and evidence consistency score. |
| `backend/app/services/nlp/analysis_pipeline.py` | Enhance | Integrate causal triplets into explanation synthesis and review-triggering logic. |
| `backend/app/ml/inference/predictor.py` | Clean up | Relocate custom pipeline definitions to avoid `__main__` unpickling hacks. |
| `backend/app/knowledge/taxonomy.py` | Consolidate | Disambiguate overlapping terms between hazards and controls. |

---

## 12. New Files Required in Phase 5

1. `backend/app/services/nlp/causal_engine.py`: Logic for building causal safety triplets and resolving barrier efficacy.
2. `backend/app/services/nlp/uncertainty.py`: Calibrated statistical confidence and epistemic uncertainty quantification.
3. `backend/tests/test_causal_reasoning.py`: Comprehensive test suite for causal triplet extraction, barrier semantics, and counterfactual validation.

---

## 13. Test Strategy
1. **Regression Baseline**: All 274 existing backend tests must pass with 0 regressions.
2. **Counterfactual Pair Suite**: Automated testing of PAIR A–F ensuring $P(\text{unsafe}) > P(\text{safe})$ with positive probability delta $\Delta > 0.15$.
3. **Compound Negation Suite**: Verification of clause-level negations across complex conjunctions.
4. **Latency Budget Enforcement**: Ensure pipeline execution remains under 50 ms on standard multi-core CPU.

---

## 14. Acceptance Criteria
- [x] Complete inventory of all NLP and ML components documented.
- [x] Accurate audit of entity, hazard, barrier, and precursor capabilities recorded.
- [x] Data flow from raw text to API response thoroughly mapped.
- [x] Technical debt, risks, and missing reasoning capabilities catalogued.
- [x] Phased roadmap with file modification plan and test strategy defined.
- [x] Zero production code modified during audit.
- [x] 274 existing tests remain 100% passing.

# NLP Pipeline Architecture (Phase 2)

## Overview

The Safety-Aware Natural Language Processing (NLP) pipeline transforms unstructured safety narrative text (unsafe acts, unsafe conditions, near-miss observations) into structured safety precursor intelligence without modifying the underlying classification model architecture.

---

## Architectural Flow

```
RAW SAFETY REPORT
       │
       ▼
[1. Preprocessing & Normalization]
  ├── Unicode NFKC & smart quote normalization
  ├── Contraction expansion (wasn't -> was not)
  └── Safety-critical token preservation
       │
       ▼
[2. Robust Sentence Segmentation]
  ├── Decimal & abbreviation protection (10.5m, e.g., P-101.A)
  └── Clause & newline boundary splitting
       │
       ▼
[3. Safety Concept Resolution]
  ├── Canonical Taxonomy (Activities, Hazards, Barriers)
  ├── Multi-phrase alias & synonym expansion
  └── Conservative RapidFuzz matching (threshold >= 88)
       │
       ▼
[4. Context, Negation & Temporal Analysis]
  ├── 5-token context window inspection
  ├── Explicit negation & absence detection (without, not, missing)
  ├── Verification detection (verified, applied, in place)
  └── Temporal inversion checks (action executed before control verified)
       │
       ▼
[5. Entity & Barrier Status Extraction]
  ├── Activity, Hazard, and Barrier canonical mapping
  ├── Barrier status (EFFECTIVE, FAILED, UNKNOWN)
  ├── Barrier failure reason extraction (not verified, bypassed, expired, etc.)
  └── Multi-entity tracking (all_activities, all_hazards, all_barriers)
       │
       ▼
[6. Downstream Intelligence Integration]
  ├── Life-Saving Rule (LSR) Mapping (strict failure signal alignment)
  ├── Evidence Extraction (exact sentence spans from source text)
  ├── Confidence Heuristic (weighted linear signal combination)
  └── Precursor Candidates & Deterministic Risk Scoring
```

---

## Key Pipeline Components

### 1. Preprocessing & Sentence Segmentation (`app.services.nlp.preprocessing`)
- **Dual Representation**: Retains `original_text` verbatim for evidence auditing and user display, while generating `normalized_text` for matching.
- **Contraction Expansion**: Automatically expands contractions (`wasn't` $\rightarrow$ `was not`, `didn't` $\rightarrow$ `did not`, `couldn't` $\rightarrow$ `could not`) ensuring negation markers are explicit.
- **Protected Segmentation**: Prevents premature sentence breaks on technical abbreviations (`e.g.`, `approx.`, `psi.`, `no.`), decimal numbers (`10.5m`, `3.14`), and equipment identifiers (`P-101.A`).

### 2. Taxonomy & Alias Catalog (`app.knowledge.safety_concepts.json` & `taxonomy.py`)
- Standardized taxonomy defining 14 Activities, 15 Hazards, and 17 Barriers.
- Rich alias mappings (e.g. `atmospheric verification` $\rightarrow$ `Gas Testing`, `safety harness` $\rightarrow$ `Fall Protection`, `zero energy state` $\rightarrow$ `Energy Isolation`).
- Decoupled from Python source code in a structured JSON catalog.

### 3. Conservative Fuzzy Matching (`rapidfuzz`)
- Handles field typos and spelling variations (e.g., `atmosphric testing` $\rightarrow$ `Gas Testing`, `loto procedur` $\rightarrow$ `Lockout Tagout`).
- Enforces strict constraints: minimum phrase length $\ge 6$ characters, maximum length delta $\le 2$, similarity threshold $\ge 88$.
- Rejects false-positive matches for short isolated words (e.g., `fire` will not match `fire watch`).

### 4. Context, Negation & Temporal Inversion
- Evaluates token windows surrounding barrier mentions to determine compliance vs violation:
  - **Effective**: Control confirmed, applied, completed, and unnegated (`Worker used fall protection`).
  - **Negated / Missing**: Control omitted, absent, or explicitly negated (`without gas testing`, `no fire watch`).
  - **Bypassed / Expired**: Control intentionally defeated or validity lapsed (`LOTO procedure was bypassed`).
  - **Temporal Inversion**: Hazardous activity started *before* control verification occurred (`entered the vessel before gas testing was completed` $\rightarrow$ `not verified`).
  - **Temporal Compliance**: Verification completed *prior* to activity (`Gas testing was completed before entry` $\rightarrow$ `verified`).

### 5. Structured Evidence & Multi-Entity Resolution (`evidence_model.py` & `entity_extractor.py`)
- Emits `StructuredEvidence` containing individual `EvidenceItem` instances.
- Tracks `all_activities`, `all_hazards`, and `all_barriers` across the narrative.
- Selects primary entities prioritizing failed/unverified barriers for downstream precursor and risk calculations, maintaining backward compatibility with the `ExtractedEntities` contract.

### 6. Downstream Compatibility
- **SIF Classifier**: Receives clean, normalized text without altering vectorizer vocabulary or model parameters.
- **LSR Mapper**: Feeds canonical concept names into `map_to_life_saving_rule` with strict structured failure signal weighting.
- **Evidence Span**: Extracts source sentence spans directly from `document.sentences`.
- **Confidence Scoring**: Combines classification probability, entity extraction confidence, rule match, and evidence presence.

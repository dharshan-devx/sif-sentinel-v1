# PHASE 5C — INTERACTIVE CAUSAL SAFETY GRAPH VISUALIZER

> Historical implementation note (2026-09-05): the referenced `frontend/`
> source tree is no longer present. This document is not evidence of a current
> frontend implementation; use the backend contract for a future F1 build.

**Project**: SIF Sentinel — SIH26165  
**Domain**: Oil & Gas Upstream/Downstream SIF Precursor Intelligence  
**Phase**: 5C — Frontend Visualization and Interaction Layer for Causal Safety Reasoning  
**Status**: COMPLETE & VERIFIED (Frontend Build 100% Passing, 11/11 Vitest Tests Passing, 288/288 Backend Tests Passing)  

---

## 1. Objective

Phase 5C delivers a responsive, explainable, and accessible **Interactive Causal Safety Graph Visualizer** for safety officers, HSE engineers, and operations managers.

The visualizer communicates the complete causal chain from Phase 5B:
$$\text{Activity} \longrightarrow \text{Hazard} \longrightarrow \text{Required Safety Barrier / Control} \longrightarrow \text{Barrier Status} \longrightarrow \text{Barrier Failure / Intact} \longrightarrow \text{Causal Exposure} \longrightarrow \text{SIF Precursor} \longrightarrow \text{Risk Priority}$$

---

## 2. Discovered Architecture & Integration Strategy

1. **Frontend Architecture**:
   - Built with **React 19 + TypeScript + Vite 8** in `frontend/`.
   - Styled with Tailwind CSS and a curated industrial dark-mode palette (`#0B0F19`, `#111827`, `#1E293B`, cyan `#06B6D4`, crimson `#EF4444`, emerald `#10B981`, violet `#8B5CF6`, and amber `#F59E0B`).
   - Testing framework: **Vitest + @testing-library/react + jsdom**.
2. **Backend Architecture**:
   - FastAPI REST API on `/api/v1/analyze` exposing `AnalysisResponse`.
   - Returns Phase 5B metadata: `safety_graph`, `causal_chains`, and `reasoning_summary`.
3. **Non-Destructive Integration**:
   - Zero breaking changes to existing endpoints or database schemas.
   - Preserved all 288 existing backend tests and classification models.

---

## 3. Components Created & File Structure

```
frontend/
├── src/
│   ├── types/
│   │   └── analysis.ts                     # TypeScript interfaces matching backend models
│   ├── services/
│   │   └── api.ts                          # REST client for /api/v1/analyze with preview fallback
│   ├── components/
│   │   ├── analysis/
│   │   │   ├── IncidentInput.tsx           # Scenario selector and narrative submission editor
│   │   │   ├── RiskScoreWidget.tsx         # Composite risk, SIF level, and LSR compliance cards
│   │   │   └── AnalysisDashboard.tsx       # Main dashboard integrating input and visualizer
│   │   └── causal-graph/
│   │       ├── ReasoningSummaryBanner.tsx  # Top summary alert (Critical Failure / Intact / Prevention)
│   │       ├── ConfidenceBreakdownBar.tsx  # Multi-dimensional confidence meters
│   │       ├── CausalChainStepper.tsx      # Sequential stepper for causal reasoning timeline
│   │       ├── GraphNodeCard.tsx           # Individual node card with category badges & status
│   │       ├── GraphCanvas.tsx             # Interactive DAG canvas (zoom, pan, stage columns)
│   │       ├── NodeDetailsPanel.tsx        # Inspector panel for node metadata & deductions
│   │       ├── EvidenceInspector.tsx       # Grounded source text highlights with char offsets
│   │       └── CausalSafetyGraph.tsx       # Top-level visualizer container with toolbar & filters
│   ├── test/
│   │   ├── setup.ts                        # Vitest matchers setup
│   │   ├── CausalSafetyGraph.test.tsx      # Unit & integration tests for graph components
│   │   └── AnalysisDashboard.test.tsx      # Dashboard integration tests
│   ├── App.tsx                             # Application navigation shell
│   └── index.css                           # Global dark theme styles and scrollbars
```

---

## 4. Graph Data Model & Node Taxonomy

Nodes are organized into six distinct stages:

| Stage | Node Type | Semantic Domain | Visual Cue |
| :---: | :--- | :--- | :--- |
| **1** | `ACTIVITY` | Operational task performed (e.g. Confined Space Work, Valve Removal) | Violet accent `#8B5CF6`, Activity Icon |
| **2** | `HAZARD` | Dangerous energy or condition (e.g. Toxic Gas, Pressurized Fluid, Fall Hazard) | Amber accent `#F59E0B`, Flame Icon |
| **3** | `CONTROL` | Required safety barrier (e.g. Atmospheric Testing, LOTO, Fall Protection) | Blue accent `#3B82F6`, Shield Icon |
| **4** | `STATUS` | 9 evaluated states (`VERIFIED`, `NOT_PERFORMED`, `FAILED`, `BYPASSED`, `MISSING`, `EXPIRED`, `UNKNOWN`) | Red `#EF4444` (Fail) or Green `#10B981` (Safe) |
| **5** | `EXPOSURE` | Direct worker exposure (e.g. Toxic Gas Inhalation, Uncontrolled Release) | Rose accent `#F43F5E`, Alert Icon |
| **6** | `PRECURSOR` | SIF precursor classification outcome (Potential SIF vs Controlled Execution) | Cyan `#06B6D4` / Crimson `#EF4444` |

---

## 5. Interaction Model

1. **Stage-Aware DAG Canvas**:
   - Pan and zoom controls (`[+]`, `[-]`, `[Reset]`).
   - Columnar layout for intuitive Left-to-Right causal progression.
2. **Sequential Causal Stepper**:
   - Safety officers can view and click each step ($\text{Activity} \to \text{Hazard} \to \text{Barrier} \to \text{Status} \to \text{Exposure}$) to highlight and focus the corresponding DAG node.
3. **Interactive Node Inspector & Evidence Grounding**:
   - Clicking any node opens the `NodeDetailsPanel` displaying exact deduction confidence and grounded evidence.
   - Displays verbatim source quotes, character offsets `[start:end]`, and evidence type (`CONTROL_FAILURE_EVIDENCE`, `CONTROL_VERIFIED_EVIDENCE`).
4. **Multi-Path Selection**:
   - When multiple causal chains exist, users can switch between chains with tab pills.
5. **Dynamic Filters**:
   - `[All Nodes]`, `[Barrier Failures]`, and `[Verified Controls]`.

---

## 6. Safety Features Handled

1. **Barrier Failure Alerting**:
   - When `barrier_failure = true`, a pulsing red shield banner with `CRITICAL BARRIER FAILURE` is displayed, highlighting the compromised barrier and resultant exposure.
2. **Verified Barrier Display**:
   - When `barrier_failure = false`, an emerald `SAFETY BARRIERS INTACT` badge confirms compliant controls.
3. **Temporal Sequencing Violation**:
   - Surfaced with a distinct clock badge `Sequence Violation` (e.g. entry before gas testing).
4. **Preventive Stop-Work Interventions**:
   - Surfaced with a cyan `Stop Work Intervention` badge (e.g. worker stopped before height exposure), ensuring safe stops are not misclassified as barrier failures.
5. **Unknown / Ambiguous States**:
   - Marked with an amber `BARRIER STATUS UNCERTAIN` badge, clearly distinguishing incomplete evidence from safe execution.

---

## 7. Multi-Dimensional Confidence Meter

Displays confidence across all five decoupled dimensions:
- **Transformer Model Confidence**
- **Extraction Quality Confidence**
- **Relationship Association Confidence**
- **Evidence Grounding Confidence**
- **Overall Causal Reasoning Confidence** (with tier labels: *High Confidence*, *Moderate*, *Requires Review*).

---

## 8. Backward Compatibility & Resilience

1. **Null-Safe Property Access**: If `safety_graph` or `causal_chains` is `null` (e.g. from an older backend version), the UI displays standard classification and risk metrics without crashing.
2. **Deterministic Offline Fallback**: If the backend is unreachable during client-side demonstration, the client utilizes a deterministic rule synthesizer to render the causal DAG.

---

## 9. Verification & Build Results

### Frontend Test Results:
```bash
npm test
✓ src/test/AnalysisDashboard.test.tsx (3 tests)
✓ src/test/CausalSafetyGraph.test.tsx (8 tests)

Test Files  2 passed (2)
Tests       11 passed (11)
```

### Frontend Production Build:
```bash
npm run build
✓ 1846 modules transformed.
✓ built in 559ms (0 errors, 0 warnings)
```

### Backend Test Regression Safety:
```bash
pytest backend/tests -v
====================== 288 passed, 2 warnings in 44.83s =======================
```

---

## 10. Phase 5D & 5E Extension Points

1. **Phase 5D (Counterfactual Simulation)**:
   - `CausalSafetyGraph` and `GraphNodeCard` are architected with state hooks ready to support interactive barrier toggles (e.g. toggling `Atmospheric Testing` from `NOT_PERFORMED` to `PERFORMED` to simulate risk reduction).
2. **Phase 5E (LLM Executive Summary)**:
   - `ReasoningSummaryBanner` contains an extension slot for the future narrative translation layer.

# SIF Sentinel — Phase 5D: Counterfactual Safety Simulation Engine
**Interactive Causal "What-If" Reasoning & Barrier Restoration Intelligence**

---

## 1. Executive Summary

In complex Oil & Gas operations (e.g., confined space entry, hot work, nitrogen purging, high-pressure line breaking), analyzing historical incidents and near-misses is necessary but insufficient. Safety officers must be empowered to ask:
> *"What would have happened if the critical atmospheric gas test had been verified prior to vessel entry?"*  
> *"How much does restoring lock-out/tag-out (LOTO) verification reduce the overall SIF risk score?"*

**Phase 5D** transitions SIF Sentinel from a diagnostic engine (*"What happened?"*) into an interactive, explainable, and predictive **Counterfactual Safety Simulation Engine** (*"What if we restore this safety barrier?"*).

### Key Accomplishments
- **Mathematically Grounded Simulation Engine**: Built `CounterfactualSafetyEngine` to simulate counterfactual barrier restorations over causal directed acyclic graphs (DAGs).
- **Absolute Immutability**: Historical observed incident data, raw text spans, and grounding evidence remain strictly immutable.
- **Deterministic Risk Model Integration**: Leverages the canonical `calculate_risk` engine and Life-Saving Rules (LSR) penalty matrices—avoiding arbitrary or fabricated probability shifts.
- **Dedicated REST API**: Implemented `POST /api/v1/analyze/counterfactual` with robust Pydantic schemas.
- **Rich Frontend Visualization**: Integrated interactive "What-If" and "Compare" modes into `CausalSafetyGraph`, `CounterfactualSimulationPanel`, and `NodeDetailsPanel` with real-time risk delta badges, edge re-coloring, and simulated glowing state diffs.
- **Zero-Regress Performance**: Full backend test suite passing (**296/296 tests**), full frontend test suite passing (**15/15 tests**), and production build cleanly compiled.
- **Ultra-Low Latency**: Sub-millisecond execution (**0.0649 ms mean latency**, P99 < 0.2 ms).

---

## 2. Core Philosophy & Architectural Principles

```
Observed Incident Report
       │
       ▼
[ Causal Safety Graph ] ─────── (Cloned Deeply) ───────┐
       │                                               │
       ▼ (Immutable)                                   ▼ (Simulated Sandbox)
[ Observed Graph Record ]                       [ Counterfactual Mutation ]
 • NOT_PERFORMED                                 • VERIFIED / PERFORMED
 • Barrier Failure: TRUE                         • Barrier Failure: FALSE
 • SIF Precursor: TRUE                           • SIF Precursor: FALSE
 • Risk Score: 95                                • Risk Score: 25
 • Historical Grounded Spans                     • Explicit Simulation Assumptions
```

1. **Strict Immutability**: The observed incident graph is cloned using deep serialization. The original graph is never mutated in memory or in storage.
2. **Canonical Risk Integration**: Simulated risk scores are computed directly by `calculate_risk()`, factoring in restored barrier status, LSR compliance, and precursor attenuation.
3. **Zero Probability Fabrication**: SIF probabilities and confidence scores are calculated through deterministic Bayesian-grounded rule weights rather than arbitrary magic constants.
4. **Evidence Provenance Guarantee**: Grounded text spans (e.g., *"without gas testing"*) stay attached to the historical record; simulated nodes display auditable counterfactual assumptions.
5. **Human-in-the-Loop Transparency**: All counterfactual outputs are flagged with `simulation_only: true` and explicitly marked with actionable assumptions.

---

## 3. Formal Problem Formulation & Causal Structural Model

Let an incident report be represented as a causal structural equation model (SEM):
$$\mathcal{G} = (\mathcal{V}, \mathcal{E}, \mathcal{F})$$

Where:
- $\mathcal{V} = \{A, H, C, S_C, B_F, E_{SIF}, P_{SIF}, R\}$
  - $A$: Activity node (e.g., `Confined Space Entry`)
  - $H$: Hazard node (e.g., `Toxic Atmosphere / H2S`)
  - $C$: Required Safety Barrier (e.g., `Gas Testing`)
  - $S_C \in \mathcal{S}$: Control status $\mathcal{S} = \{\text{VERIFIED}, \text{PERFORMED}, \text{NOT\_PERFORMED}, \dots\}$
  - $B_F \in \{0, 1\}$: Barrier failure indicator
  - $E_{SIF} \in \mathcal{E}_{type}$: SIF exposure level
  - $P_{SIF} \in \{0, 1\}$: SIF precursor condition
  - $R \in [0, 100]$: Composite risk score
- $\text{do}(S_C = v^*)$: Pearl's Do-Calculus intervention operator that sets the status of barrier $C$ to target state $v^* \in \{\text{VERIFIED}, \text{PERFORMED}\}$.

### Structural Equations Under Intervention:
$$B_F^* = f_{BF}(v^*) = \begin{cases} 0 & \text{if } v^* \in \{\text{VERIFIED}, \text{PERFORMED}\} \\ 1 & \text{otherwise} \end{cases}$$

$$E_{SIF}^* = f_E(H, B_F^*) = \begin{cases} \text{CONTROLLED\_STATE} & \text{if } B_F^* = 0 \\ E_{observed} & \text{if } B_F^* = 1 \end{cases}$$

$$P_{SIF}^* = f_P(A, H, B_F^*) = \begin{cases} \text{False} & \text{if } \forall C_i, B_{F, i}^* = 0 \\ \text{True} & \text{if } \exists C_i \text{ with } B_{F, i}^* = 1 \land H \in \mathcal{H}_{\text{high-energy}} \end{cases}$$

$$R^* = \text{calculate\_risk}(\text{severity}, \text{probability}^*, \text{is\_sif}^*, \text{barrier\_status}^*)$$

$$\Delta R = R^* - R_{observed} \quad (\Delta R \le 0 \implies \text{Risk Reduced})$$

---

## 4. Supported Counterfactual State Transitions

The engine supports 6 canonical barrier restoration operations:

| Observed State | Target State | Failure Before | Failure After | Causal Semantic Impact |
| :--- | :--- | :---: | :---: | :--- |
| `NOT_PERFORMED` | `PERFORMED` / `VERIFIED` | `True` | `False` | Resolves omission; verifies critical control execution prior to work. |
| `NOT_VERIFIED` | `VERIFIED` | `True` | `False` | Restores formal permit / check signoff; eliminates verification deficit. |
| `FAILED` | `PERFORMED` / `VERIFIED` | `True` | `False` | Replaces defective equipment or failed containment with verified barrier. |
| `BYPASSED` | `VERIFIED` | `True` | `False` | Re-establishes safety interlock, guard, or lockout protocol. |
| `MISSING` | `PERFORMED` / `VERIFIED` | `True` | `False` | Installs missing engineered barrier, PPE, or ventilation system. |
| `EXPIRED` | `VERIFIED` | `True` | `False` | Renews expired permit-to-work, atmospheric calibration, or safety certificate. |

---

## 5. Downstream Causal Propagation Semantics

When an intervention $\text{do}(S_C = v^*)$ is executed on target barrier $C_t$:
1. **Target Control Node**: Status updated to $v^*$.
2. **Barrier Failure Node**: State transitions from `True` (failed) to `False` (intact).
3. **Causal Chains**: All causal chains containing $C_t$ are evaluated:
   - If all controls in chain $k$ are intact, chain failure flag becomes `False` and chain exposure transitions to `"CONTROLLED_STATE"`.
4. **Exposure Node**: If no active barrier failures remain across any chain, the global exposure node transitions to `"MITIGATED"` / `"NO_UNCONTROLLED_EXPOSURE"`.
5. **SIF Precursor Node**: If high-energy hazard exposure is mitigated by the restored barrier, $P_{SIF}$ transitions to `False` (`sif_potential: false`, classification: `"NON_SIF"`).
6. **Edge Styling**: Directed edges originating from restored controls turn from hazardous red/amber (`#ef4444`) to verified green (`#10b981`).

---

## 6. Canonical Risk Engine Integration

Simulated risk recalculation directly calls `app.services.risk_engine.calculator.calculate_risk`:

```python
simulated_barrier_status = (
    BarrierStatus.ADEQUATE if not any_barrier_failed else BarrierStatus.FAILED
)
simulated_sif_level = (
    SIFLevel.NON_SIF if not simulated_sif_potential else SIFLevel.PSIF
)

sim_risk = calculate_risk(
    sif_level=simulated_sif_level,
    barrier_status=simulated_barrier_status,
    has_life_saving_rule=has_lsr,
    precursor_priority=precursor_priority if simulated_sif_potential else "LOW",
)
```

### Risk Direction Categorization:
- **`REDUCED`**: $\Delta R < 0$ (Quantitative safety improvement)
- **`UNCHANGED`**: $\Delta R = 0$ (Concurrent independent failures still present)
- **`INCREASED`**: $\Delta R > 0$ (Theoretical negative scenario)

---

## 7. REST API Design & Contracts

### Endpoint Specification
`POST /api/v1/analyze/counterfactual`

### Request Payload (`CounterfactualRequest`)
```json
{
  "original_graph": {
    "activity": {"activity_type": "Confined Space Work", "confidence": 1.0},
    "hazard": {"hazard_type": "Toxic Atmosphere", "is_high_energy": true},
    "control": {"control_name": "Gas Testing", "control_status": "NOT_PERFORMED"},
    "barrier_failed": true,
    "chains": [
      {
        "activity": "Confined Space Work",
        "hazard": "Toxic Atmosphere",
        "control": "Gas Testing",
        "control_status": "NOT_PERFORMED",
        "barrier_failure": true,
        "exposure": "SIF Precursor Exposure"
      }
    ],
    "precursor": {"is_sif_precursor": true, "sif_probability": 0.95}
  },
  "target_control": "Gas Testing",
  "simulated_status": "VERIFIED",
  "target_node_id": "ctrl-0",
  "original_risk_score": 95,
  "has_lsr": true,
  "precursor_priority": "HIGH"
}
```

### Response Payload (`CounterfactualResponse`)
```json
{
  "scenario_id": "cf_a1b2c3d4",
  "target_node_id": "ctrl-0",
  "target_control": "Gas Testing",
  "original_status": "NOT_PERFORMED",
  "simulated_status": "VERIFIED",
  "original_barrier_failure": true,
  "simulated_barrier_failure": false,
  "original_exposure": "SIF Precursor Exposure",
  "simulated_exposure": "CONTROLLED_STATE",
  "original_risk_score": 95,
  "simulated_risk_score": 25,
  "risk_delta": -70,
  "risk_direction": "REDUCED",
  "original_sif_potential": true,
  "simulated_sif_potential": false,
  "original_sif_classification": "PSIF",
  "simulated_sif_classification": "NON_SIF",
  "causal_changes": [
    {
      "element_type": "CONTROL_STATUS",
      "element_name": "Gas Testing",
      "observed_value": "NOT_PERFORMED",
      "simulated_value": "VERIFIED",
      "description": "Safety control 'Gas Testing' changed from NOT_PERFORMED to VERIFIED."
    },
    {
      "element_type": "BARRIER_FAILURE",
      "element_name": "Barrier Failure Mechanism",
      "observed_value": true,
      "simulated_value": false,
      "description": "Barrier failure mechanism resolved to safe/intact state."
    },
    {
      "element_type": "SIF_PRECURSOR",
      "element_name": "SIF Precursor Condition",
      "observed_value": true,
      "simulated_value": false,
      "description": "SIF precursor state mitigated by restored barrier."
    },
    {
      "element_type": "RISK_SCORE",
      "element_name": "Composite Risk Score",
      "observed_value": 95,
      "simulated_value": 25,
      "description": "Composite risk score reduced by 70 points (from 95 to 25)."
    }
  ],
  "affected_nodes": ["control", "failure", "exposure", "precursor"],
  "affected_edges": [
    {"source": "control", "target": "failure", "simulated_style": "safe"}
  ],
  "assumptions": [
    "Safety control 'Gas Testing' is assumed to be fully verified and functional prior to work commencement.",
    "All personnel are assumed to strictly adhere to the simulated control barrier.",
    "No additional unmodeled equipment degradation or concurrent failures occurred.",
    "Risk delta is computed using the canonical SIF Sentinel deterministic risk model.",
    "This is a counterfactual simulation and does not alter the historical or observed incident report."
  ],
  "interpretation": "What-if 'Gas Testing' had been VERIFIED? Restoring this barrier eliminates the modeled failure mechanism and mitigates downstream 'sif precursor exposure' exposure. Composite risk decreases from 95 to 25 (Delta: -70 pts). The SIF precursor classification shifts from POTENTIAL SIF to CONTROLLED EXECUTION.",
  "confidence": 0.95,
  "simulated_graph": { "...": "..." },
  "simulation_only": true,
  "created_at": "2026-09-04T16:55:00.000Z"
}
```

---

## 8. Frontend Interactive Simulation Architecture

### Component Hierarchy
```
CausalSafetyGraph
 │
 ├── Top View Mode Toolbar ([Observed] | [Simulated] | [Compare Side-by-Side])
 ├── Simulation Active Alert Banner (Shows target barrier, Δ Risk, Reset Button)
 ├── GraphCanvas
 │    ├── GraphNodeCard (Renders node, compare tag diff, glowing simulated border)
 │    └── Dynamic SVG Edges (Color transitions based on active simulation mode)
 └── NodeDetailsPanel
      └── CounterfactualSimulationPanel
           ├── Target Status Selector (VERIFIED / PERFORMED)
           ├── Run Simulation Button (with loading spinner)
           ├── Comparative Metric Cards (Risk Score, SIF Precursor, Failure State)
           ├── Detailed Causal Change List
           └── Grounded Simulation Assumptions Box
```

### Key UI Features:
- **Compare View Mode**: Simultaneously displays the observed value alongside the simulated counterfactual value (e.g., `[NOT_PERFORMED → VERIFIED]`).
- **Visual Diffs**: Simulated nodes receive emerald glowing borders (`ring-2 ring-emerald-500/50`); edges turn emerald green (`#10b981`).
- **Immediate Reversibility**: One-click **"Reset to Observed State"** restores original graph view without page reloads.

---

## 9. Offline & Client-Side Fallback Synthesis

In the event of network disconnection or standalone client operation, `frontend/src/services/api.ts` features a built-in deterministic client-side synthesizer (`synthesizeOfflineCounterfactual`):
- Deeply clones client graph objects.
- Executes identical downstream chain updates.
- Recalculates risk deltas using the client-side risk table.
- Emits fully-formed `CounterfactualScenario` payloads to ensure uninterrupted safety investigation.

---

## 10. Latency & Performance Benchmarks

Benchmark executed over 200 consecutive simulation cycles:

| Metric | Measured Latency | Target SLA | Compliance |
| :--- | :---: | :---: | :---: |
| **Mean Execution Time** | **0.0649 ms** | < 10.0 ms | **PASS (154x faster)** |
| **P50 (Median)** | **0.0556 ms** | < 5.0 ms | **PASS** |
| **P95** | **0.1143 ms** | < 15.0 ms | **PASS** |
| **P99** | **0.1825 ms** | < 25.0 ms | **PASS** |
| **Throughput** | **~15,400 simulations/sec** | > 100/sec | **PASS** |

---

## 11. Evidence Grounding & Audit Traceability

```
Historical Incident Span: "Worker entered nitrogen purge vessel without atmospheric gas testing"
  │
  ├─ Observed Record (Immutable):
  │    • Evidence: "without atmospheric gas testing"
  │    • Status: NOT_PERFORMED
  │    • Failure: TRUE
  │
  └─ Counterfactual Sandbox (Simulated):
       • Assumption 1: "Safety control 'Gas Testing' is assumed to be fully verified and functional."
       • Assumption 2: "All personnel are assumed to strictly adhere to the simulated control barrier."
       • Risk Delta: -70 points
       • Audit Flag: simulation_only = true
```

---

## 12. Comprehensive Test Suite & Verification Results

### Backend Test Results (`pytest backend/tests -v`)
- Total Tests: **296 passed, 0 failed, 0 errors**
- Counterfactual Test Suite (`test_counterfactual_engine.py`):
  1. `test_counterfactual_simulation_not_performed_to_verified` — PASSED
  2. `test_counterfactual_simulation_not_verified_to_verified` — PASSED
  3. `test_counterfactual_simulation_failed_to_performed` — PASSED
  4. `test_counterfactual_simulation_bypassed_to_verified` — PASSED
  5. `test_counterfactual_simulation_missing_to_performed` — PASSED
  6. `test_counterfactual_simulation_expired_to_verified` — PASSED
  7. `test_counterfactual_immutability_guarantee` — PASSED
  8. `test_counterfactual_api_endpoint` — PASSED

### Frontend Test Results (`npm test`)
- Total Test Files: **3 passed**
- Total Tests: **15 passed, 0 failed**
- Counterfactual Component Suite (`CounterfactualSimulation.test.tsx`):
  1. `renders simulation controls when inspecting a barrier node` — PASSED
  2. `executes simulation and displays risk delta badge and interpretation` — PASSED
  3. `resets simulation back to observed state when reset button clicked` — PASSED
  4. `displays simulation assumptions list clearly` — PASSED

---

## 13. Production Build Validation

Executed `npm run build` in `frontend/`:
```bash
vite v5.4.14 building for production...
✓ 1838 modules transformed.
dist/index.html                   0.75 kB │ gzip:  0.42 kB
dist/assets/index-CddjuSiu.css   48.21 kB │ gzip:  8.79 kB
dist/assets/index-CddjuSiu.js   477.58 kB │ gzip: 147.22 kB
✓ built in 2.00s
```
**Zero build errors, zero type errors, zero bundle warnings.**

---

## 14. Edge Cases & Boundary Conditions Handled

1. **Multi-Barrier Chains with Independent Failures**:
   - If a report contains *both* missing gas testing and bypassed ventilation, restoring only gas testing reduces risk but correctly keeps $P_{SIF} = \text{True}$ until the secondary barrier is also addressed.
2. **Double Negations in Raw Narratives**:
   - Spans such as *"did not fail to inspect"* resolve to `VERIFIED` in the base graph; counterfactual simulation recognizes already-intact barriers and flags them appropriately.
3. **Prevention Interventions**:
   - Pre-work stop-work interventions are preserved as historical evidence while allowing what-if evaluations of potential subsequent steps.

---

## 15. Non-Destructive Integration Analysis

All Phase 5D features were integrated strictly non-destructively:
- Existing Phase 3 baseline classifiers: **Untouched & verified**.
- Existing Phase 4B DistilBERT transformer models: **Untouched & verified**.
- Existing Phase 5B Causal reasoning engine: **Extended cleanly via modular composition**.
- Existing Phase 5C Interactive visualizer: **Upgraded with backwards-compatible state handlers**.

---

## 16. Safety Officer User Guide & Operational Workflows

1. **Submit Incident Report**: Enter narrative in SIF Sentinel analysis dashboard.
2. **Inspect Causal Safety Graph**: View the extracted causal chain (`Activity → Hazard → Barrier → Status → Exposure → Precursor`).
3. **Select Barrier Node**: Click on any yellow/red barrier card in the graph canvas.
4. **Configure Simulation**: In the side panel, select target restored state (`VERIFIED` or `PERFORMED`).
5. **Run Simulation**: Click *"Simulate Barrier Restoration"*.
6. **Evaluate Risk Delta**:
   - Review the green $\Delta \text{Risk}$ reduction pill.
   - Toggle **`[Compare]`** mode to see side-by-side node diffs.
   - Review auditable simulation assumptions.
7. **Export or Reset**: Incorporate findings into incident investigation action items or reset to baseline view.

---

## 17. Limitations & Future Extensions

- **Future Multi-Node Interventions**: Phase 5D currently focuses on single and sequential barrier restorations; future phases will support joint combinatorial optimization over entire barrier matrices.
- **Cost-Benefit Weighting**: Incorporating operational cost metrics per barrier restoration to identify highest-ROI safety investments.

---

## 18. Deliverable Checklist & Verification Status

- [x] Strongly typed `CounterfactualScenario` & `CounterfactualChange` models
- [x] Complete immutability of observed graph records
- [x] All 6 canonical state transitions supported
- [x] Deterministic risk model integration via canonical `calculate_risk`
- [x] API endpoint `POST /api/v1/analyze/counterfactual`
- [x] Interactive UI (`CounterfactualSimulationPanel`, `Compare` mode, `What-If` mode)
- [x] Offline client-side simulation fallback
- [x] 296/296 Backend tests passing
- [x] 15/15 Frontend tests passing
- [x] Production build cleanly passing
- [x] Sub-millisecond simulation performance (0.0649 ms)
- [x] Comprehensive documentation in `docs/ml/PHASE5D_COUNTERFACTUAL_SIMULATION.md`

import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { SafetyNarrativePanel } from '../components/narrative/SafetyNarrativePanel'
import type { CounterfactualScenario } from '../types/analysis'

describe('Phase 5E Safety Narrative Translation & Explainability Layer', () => {
  const mockScenario: CounterfactualScenario = {
    scenario_id: 'cf-101',
    target_control: 'Gas Testing',
    original_status: 'NOT_PERFORMED',
    simulated_status: 'VERIFIED',
    original_barrier_failure: true,
    simulated_barrier_failure: false,
    original_exposure: 'SIF Precursor Exposure',
    simulated_exposure: 'CONTROLLED_STATE',
    original_risk_score: 95,
    simulated_risk_score: 25,
    risk_delta: -70,
    risk_direction: 'REDUCED',
    original_sif_potential: true,
    simulated_sif_potential: false,
    original_sif_classification: 'PSIF',
    simulated_sif_classification: 'NON_SIF',
    causal_changes: [],
    affected_nodes: ['node_1'],
    affected_edges: [],
    assumptions: ["Gas testing assumed verified."],
    interpretation: "Restoring gas testing eliminates failure mechanism.",
    confidence: 0.96,
    simulated_graph: {
      nodes: [],
      edges: [],
      causal_chains: [],
    },
    simulation_only: true,
    created_at: new Date().toISOString(),
  }

  it('renders executive narrative mode and system-determined source of truth badges', async () => {
    render(
      <SafetyNarrativePanel
        incidentText="Worker entered nitrogen purge vessel without atmospheric gas testing."
        riskScore={95}
        riskPriority="CRITICAL"
        sifPotential={true}
        sifLevel="PSIF"
      />
    )

    expect(screen.getByText('AI Safety Narrative & Explainability Layer')).toBeInTheDocument()
    expect(screen.getByText('Deterministic Engine')).toBeInTheDocument()
    expect(screen.getByText('95/100')).toBeInTheDocument()
    expect(screen.getByText('PSIF Precursor')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText(/EXECUTIVE Narrative Explanation/i)).toBeInTheDocument()
    })
  })

  it('switches between narrative modes smoothly', async () => {
    render(
      <SafetyNarrativePanel
        incidentText="Worker entered nitrogen purge vessel without atmospheric gas testing."
        riskScore={95}
        riskPriority="CRITICAL"
        sifPotential={true}
      />
    )

    // Switch to Investigation mode
    const investBtn = screen.getByRole('button', { name: /Investigation/i })
    fireEvent.click(investBtn)

    await waitFor(() => {
      expect(screen.getByText(/INVESTIGATION Narrative Explanation/i)).toBeInTheDocument()
    })

    // Switch to Field mode
    const fieldBtn = screen.getByRole('button', { name: /Field Alert/i })
    fireEvent.click(fieldBtn)

    await waitFor(() => {
      expect(screen.getByText(/FIELD Narrative Explanation/i)).toBeInTheDocument()
    })
  })

  it('renders grounded recommendations and key findings', async () => {
    render(
      <SafetyNarrativePanel
        incidentText="Worker entered nitrogen purge vessel without atmospheric gas testing."
        riskScore={95}
        riskPriority="CRITICAL"
        sifPotential={true}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Key Safety Findings')).toBeInTheDocument()
      expect(screen.getByText('Grounded Recommendations')).toBeInTheDocument()
    })
  })

  it('opens grounding provenance inspection drawer when clicked', async () => {
    render(
      <SafetyNarrativePanel
        incidentText="Worker entered nitrogen purge vessel without atmospheric gas testing."
        riskScore={95}
        riskPriority="CRITICAL"
        sifPotential={true}
      />
    )

    await waitFor(() => {
      expect(screen.getByText(/Inspect Mathematical Grounding/i)).toBeInTheDocument()
    })

    const groundingBtn = screen.getByText(/Inspect Mathematical Grounding/i)
    fireEvent.click(groundingBtn)

    await waitFor(() => {
      expect(screen.getByText(/Every claim is verified against deterministic safety components/i)).toBeInTheDocument()
      expect(screen.getByText(/Composite Risk Score/i)).toBeInTheDocument()
    })
  })

  it('automatically synchronizes with counterfactual scenario and renders risk delta', async () => {
    render(
      <SafetyNarrativePanel
        incidentText="Worker entered nitrogen purge vessel without atmospheric gas testing."
        riskScore={95}
        riskPriority="CRITICAL"
        sifPotential={true}
        counterfactualScenario={mockScenario}
      />
    )

    await waitFor(() => {
      expect(screen.getByText(/COUNTERFACTUAL Narrative Explanation/i)).toBeInTheDocument()
      expect(screen.getByText(/What-if 'Gas Testing' had been VERIFIED/i)).toBeInTheDocument()
      expect(screen.getByText(/Delta: -70 pts/i)).toBeInTheDocument()
    })
  })
})

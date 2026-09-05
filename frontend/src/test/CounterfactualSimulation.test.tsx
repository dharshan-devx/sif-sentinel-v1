import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { CounterfactualSimulationPanel } from '../components/causal-graph/CounterfactualSimulationPanel'
import { CausalSafetyGraph } from '../components/causal-graph/CausalSafetyGraph'
import type { GraphNode, CausalChain, SafetyReasoningGraph, CounterfactualScenario } from '../types/analysis'

const mockControlNode: GraphNode = {
  id: 'control:Gas Testing',
  type: 'CONTROL',
  label: 'Gas Testing',
  status: 'NOT_PERFORMED',
  confidence: 0.95,
}

const mockChain: CausalChain = {
  activity: 'Confined Space Work',
  hazard: 'Hazardous Atmosphere',
  control: 'Gas Testing',
  control_status: 'NOT_PERFORMED',
  barrier_failure: true,
  exposure: 'Toxic gas inhalation',
  relationship: 'REQUIRES_BARRIER',
  evidence: [],
  confidence: 0.95,
}

const mockGraph: SafetyReasoningGraph = {
  nodes: [
    { id: 'act_1', type: 'ACTIVITY', label: 'Confined Space Work' },
    { id: 'haz_1', type: 'HAZARD', label: 'Hazardous Atmosphere' },
    mockControlNode,
    { id: 'stat_1', type: 'STATUS', label: 'NOT_PERFORMED', status: 'NOT_PERFORMED' },
    { id: 'exp_1', type: 'EXPOSURE', label: 'Toxic gas inhalation' },
    { id: 'prec_1', type: 'PRECURSOR', label: 'Potential SIF' },
  ],
  edges: [],
  causal_chains: [mockChain],
  summary: 'Confined space entry without gas testing.',
}

const mockScenario: CounterfactualScenario = {
  scenario_id: 'sim_test123',
  target_control: 'Gas Testing',
  original_status: 'NOT_PERFORMED',
  simulated_status: 'VERIFIED',
  original_barrier_failure: true,
  simulated_barrier_failure: false,
  original_exposure: 'Toxic gas inhalation',
  simulated_exposure: 'CONTROLLED_ACTIVITY',
  original_risk_score: 86,
  simulated_risk_score: 31,
  risk_delta: -55,
  risk_direction: 'REDUCED',
  original_sif_potential: true,
  simulated_sif_potential: false,
  original_sif_classification: 'PSIF',
  simulated_sif_classification: 'NON_SIF',
  causal_changes: [
    {
      element_type: 'CONTROL_STATUS',
      element_name: 'Gas Testing',
      observed_value: 'NOT_PERFORMED',
      simulated_value: 'VERIFIED',
      description: "Barrier 'Gas Testing' changed to VERIFIED.",
    },
  ],
  affected_nodes: ['control:Gas Testing', 'stat_1', 'exp_1'],
  affected_edges: [],
  assumptions: [
    "Gas testing is assumed to be completed before entry.",
    "No other barrier states were changed.",
    "The simulation modifies only the selected control.",
    "Risk change is calculated using the existing deterministic risk model.",
    "This is a counterfactual simulation.",
  ],
  interpretation: "What-if gas testing had been verified? Risk score decreases from 86 to 31.",
  confidence: 0.95,
  simulated_graph: mockGraph,
  simulation_only: true,
  created_at: new Date().toISOString(),
}

describe('Counterfactual Simulation Component Suite', () => {
  it('renders simulation panel for selected control node', () => {
    const handleUpdate = vi.fn()
    render(
      <CounterfactualSimulationPanel
        node={mockControlNode}
        activeChain={mockChain}
        safetyGraph={mockGraph}
        riskScore={86}
        activeScenario={null}
        onScenarioUpdate={handleUpdate}
      />
    )

    expect(screen.getByText(/What-If Safety Simulation/i)).toBeInTheDocument()
    expect(screen.getByText(/'Gas Testing'/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^Simulate$/i })).toBeInTheDocument()
  })

  it('runs simulation and triggers scenario update', async () => {
    const handleUpdate = vi.fn()
    render(
      <CounterfactualSimulationPanel
        node={mockControlNode}
        activeChain={mockChain}
        safetyGraph={mockGraph}
        riskScore={86}
        activeScenario={null}
        onScenarioUpdate={handleUpdate}
      />
    )

    const simulateBtn = screen.getByRole('button', { name: /^Simulate$/i })
    fireEvent.click(simulateBtn)

    await waitFor(() => {
      expect(handleUpdate).toHaveBeenCalled()
    })
  })

  it('renders simulation results with quantitative risk delta and comparisons', () => {
    const handleUpdate = vi.fn()
    render(
      <CounterfactualSimulationPanel
        node={mockControlNode}
        activeChain={mockChain}
        safetyGraph={mockGraph}
        riskScore={86}
        activeScenario={mockScenario}
        onScenarioUpdate={handleUpdate}
      />
    )

    expect(screen.getByText(/Simulation Active/i)).toBeInTheDocument()
    expect(screen.getByText(/-55 Pts/i)).toBeInTheDocument()
    expect(screen.getByText(/What-if gas testing had been verified/i)).toBeInTheDocument()
  })

  it('renders full graph with simulation banner and view mode toggle', () => {
    render(
      <CausalSafetyGraph
        safetyGraph={mockGraph}
        causalChains={[mockChain]}
        reasoningSummary="Incident report."
        sifPotential={true}
        riskScore={86}
      />
    )

    // Select the control node
    const ctrlNodes = screen.getAllByText('Gas Testing')
    fireEvent.click(ctrlNodes[0])

    expect(screen.getByText(/What-If Safety Simulation/i)).toBeInTheDocument()
  })
})

import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CausalSafetyGraph } from '../components/causal-graph/CausalSafetyGraph'
import { ReasoningSummaryBanner } from '../components/causal-graph/ReasoningSummaryBanner'
import { CausalChainStepper } from '../components/causal-graph/CausalChainStepper'
import { ConfidenceBreakdownBar } from '../components/causal-graph/ConfidenceBreakdownBar'
import type { SafetyReasoningGraph, CausalChain } from '../types/analysis'

const mockChainFailure: CausalChain = {
  activity: 'Confined Space Work',
  hazard: 'Hazardous Atmosphere / Toxic Gas',
  control: 'Atmospheric Testing / Gas Monitoring',
  control_status: 'NOT_PERFORMED',
  barrier_failure: true,
  exposure: 'Toxic gas inhalation',
  relationship: 'REQUIRES_BARRIER',
  evidence: [
    {
      claim: 'Gas testing was omitted',
      evidence: 'without gas testing',
      source_span: [20, 38],
      evidence_type: 'CONTROL_FAILURE_EVIDENCE',
      confidence: 0.96,
    },
  ],
  confidence: 0.95,
  confidence_breakdown: {
    model_confidence: 0.95,
    extraction_confidence: 0.92,
    relationship_confidence: 0.94,
    evidence_confidence: 0.96,
    overall_reasoning_confidence: 0.94,
  },
  temporal_inversion: true,
  prevention_detected: false,
}

const mockChainSafe: CausalChain = {
  activity: 'Working at Height',
  hazard: 'Fall Hazard',
  control: 'Fall Protection Harness',
  control_status: 'VERIFIED',
  barrier_failure: false,
  exposure: 'Controlled platform',
  relationship: 'REQUIRES_BARRIER',
  evidence: [
    {
      claim: 'Harness tie-off verified',
      evidence: 'with 100% tie-off safety harness',
      source_span: [10, 42],
      evidence_type: 'CONTROL_VERIFIED_EVIDENCE',
      confidence: 0.98,
    },
  ],
  confidence: 0.97,
  temporal_inversion: false,
  prevention_detected: false,
}

const mockGraph: SafetyReasoningGraph = {
  nodes: [
    { id: 'n1', type: 'ACTIVITY', label: 'Confined Space Work', confidence: 0.95 },
    { id: 'n2', type: 'HAZARD', label: 'Hazardous Atmosphere', confidence: 0.94 },
    { id: 'n3', type: 'CONTROL', label: 'Atmospheric Testing', confidence: 0.96 },
    { id: 'n4', type: 'STATUS', label: 'NOT_PERFORMED', status: 'NOT_PERFORMED', confidence: 0.95 },
    { id: 'n5', type: 'EXPOSURE', label: 'Toxic gas inhalation', confidence: 0.92 },
    { id: 'n6', type: 'PRECURSOR', label: 'SIF Precursor', confidence: 0.98 },
  ],
  edges: [
    { id: 'e1', source: 'n1', target: 'n2', relationship: 'INVOLVES' },
    { id: 'e2', source: 'n2', target: 'n3', relationship: 'REQUIRES' },
  ],
  causal_chains: [mockChainFailure],
  summary: 'Confined space work executed without gas testing leading to high SIF potential.',
}

describe('CausalSafetyGraph Component Suite', () => {
  it('renders reasoning summary banner with barrier failure warning', () => {
    render(
      <ReasoningSummaryBanner
        summary="Critical barrier omitted"
        chains={[mockChainFailure]}
        sifPotential={true}
      />
    )
    expect(screen.getByText(/CRITICAL BARRIER FAILURE/i)).toBeInTheDocument()
    expect(screen.getByText(/Critical barrier omitted/i)).toBeInTheDocument()
    expect(screen.getByText(/Sequence Violation/i)).toBeInTheDocument()
  })

  it('renders safe barrier banner when control is verified', () => {
    render(
      <ReasoningSummaryBanner
        summary="Verified barrier intact"
        chains={[mockChainSafe]}
        sifPotential={false}
      />
    )
    expect(screen.getByText(/SAFETY BARRIERS INTACT/i)).toBeInTheDocument()
    expect(screen.getByText(/Verified barrier intact/i)).toBeInTheDocument()
  })

  it('renders prevention banner when prevention intervention is detected', () => {
    const preventionChain: CausalChain = {
      ...mockChainFailure,
      barrier_failure: false,
      prevention_detected: true,
    }
    render(
      <ReasoningSummaryBanner
        summary="Intervention stopped contractor"
        chains={[preventionChain]}
        sifPotential={false}
      />
    )
    expect(screen.getByText(/PREVENTION INTERVENTION/i)).toBeInTheDocument()
    expect(screen.getByText(/Stop Work Intervention/i)).toBeInTheDocument()
  })

  it('renders confidence breakdown metrics correctly', () => {
    render(
      <ConfidenceBreakdownBar
        breakdown={mockChainFailure.confidence_breakdown}
        overallConfidence={0.94}
      />
    )
    expect(screen.getByText(/Multi-Dimensional Confidence/i)).toBeInTheDocument()
    expect(screen.getAllByText(/94%/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/Evidence/i)).toBeInTheDocument()
    expect(screen.getByText(/Extraction/i)).toBeInTheDocument()
  })

  it('renders causal chain stepper with distinct stages', () => {
    render(
      <CausalChainStepper
        chains={[mockChainFailure]}
        selectedChainIdx={0}
        onSelectChain={() => {}}
      />
    )
    expect(screen.getByText('Confined Space Work')).toBeInTheDocument()
    expect(screen.getByText('Hazardous Atmosphere / Toxic Gas')).toBeInTheDocument()
    expect(screen.getByText('Atmospheric Testing / Gas Monitoring')).toBeInTheDocument()
    expect(screen.getByText('NOT PERFORMED')).toBeInTheDocument()
  })

  it('renders full CausalSafetyGraph with nodes, timeline, and inspector', () => {
    render(
      <CausalSafetyGraph
        safetyGraph={mockGraph}
        causalChains={[mockChainFailure]}
        reasoningSummary={mockGraph.summary}
        sifPotential={true}
        overallConfidence={0.94}
        reportText="Worker entered vessel without gas testing"
      />
    )

    // Verify presence of DAG nodes
    expect(screen.getAllByText('Confined Space Work').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Atmospheric Testing').length).toBeGreaterThan(0)

    // Verify grounded evidence appears
    expect(screen.getByText(/Grounded Source Evidence/i)).toBeInTheDocument()
    expect(screen.getByText(/"without gas testing"/i)).toBeInTheDocument()
  })

  it('renders graceful fallback when causal graph is null (backward compatibility)', () => {
    render(
      <CausalSafetyGraph
        safetyGraph={null}
        causalChains={null}
        reasoningSummary={null}
        sifPotential={false}
      />
    )
    expect(
      screen.getByText(/Causal safety reasoning is not available for this analysis report/i)
    ).toBeInTheDocument()
  })

  it('supports selecting nodes to inspect details', () => {
    render(
      <CausalSafetyGraph
        safetyGraph={mockGraph}
        causalChains={[mockChainFailure]}
        reasoningSummary={mockGraph.summary}
        sifPotential={true}
        overallConfidence={0.94}
      />
    )

    const nodeCard = screen.getByText('Atmospheric Testing')
    fireEvent.click(nodeCard)

    expect(screen.getByRole('complementary', { name: /Causal Node Details Inspector/i })).toBeInTheDocument()
  })
})

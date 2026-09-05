import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { CorrectiveActionPanel } from '../components/interventions/CorrectiveActionPanel'
import type { AnalysisResponse } from '../types/analysis'

describe('Phase 5F Corrective Action & Prevention Intelligence Layer', () => {
  const mockAnalysis: AnalysisResponse = {
    report_text: 'Worker entered nitrogen vessel without atmospheric gas testing or entry permit.',
    sif_potential: true,
    sif_level: 'PSIF',
    model_probability: 0.96,
    activity: 'Confined Space Entry',
    hazard: 'Toxic Atmosphere',
    barrier: 'Atmospheric Gas Testing',
    barrier_status: 'NOT_PERFORMED',
    barrier_failure: 'FAILED',
    life_saving_rule: 'Bypassing Safety Controls',
    rule_confidence: 0.94,
    evidence_span: 'without atmospheric gas testing',
    evidence_sentences: ['Worker entered vessel without gas test.'],
    evidence_terms: ['nitrogen', 'gas testing'],
    overall_confidence: 0.95,
    review_required: false,
    model_version: 'v1.0',
    explanation: 'Unmitigated confined space entry.',
    risk: {
      score: 95,
      priority: 'CRITICAL',
      components: [],
      version: 'v1.0',
    },
    safety_graph: {
      nodes: [
        { id: 'node_ctrl_1', type: 'CONTROL', label: 'Atmospheric Gas Testing' },
      ],
      edges: [],
      causal_chains: [
        {
          activity: 'Confined Space Entry',
          hazard: 'Toxic Atmosphere',
          control: 'Atmospheric Gas Testing',
          control_status: 'NOT_PERFORMED',
          barrier_failure: true,
          exposure: 'SIF_PRECURSOR_EXPOSURE',
          relationship: 'REQUIRES_BARRIER',
          evidence: [],
          confidence: 0.95,
        },
      ],
    },
  }

  it('renders corrective action recommendations and hierarchy of controls badges', async () => {
    render(<CorrectiveActionPanel analysis={mockAnalysis} />)

    await waitFor(() => {
      expect(
        screen.getByText('Automated Corrective Intervention Intelligence')
      ).toBeInTheDocument()
    })

    expect(screen.getAllByText(/Perform Multi-Gas Atmospheric Testing/i)[0]).toBeInTheDocument()
    expect(screen.getAllByText('4. Administrative Control')[0]).toBeInTheDocument()
  })

  it('filters actions by hierarchy level', async () => {
    render(<CorrectiveActionPanel analysis={mockAnalysis} />)

    await waitFor(() => {
      expect(screen.getByText(/All Actions/i)).toBeInTheDocument()
    })

    const adminBtn = screen.getByRole('button', { name: /Administrative/i })
    fireEvent.click(adminBtn)

    expect(screen.getAllByText(/Perform Multi-Gas Atmospheric Testing/i)[0]).toBeInTheDocument()
  })


  it('triggers simulation when clicking Simulate This Intervention', async () => {
    const handleSimulate = vi.fn()
    render(
      <CorrectiveActionPanel
        analysis={mockAnalysis}
        onSimulateIntervention={handleSimulate}
      />
    )

    await waitFor(() => {
      expect(screen.getAllByText('Simulate This Intervention')[0]).toBeInTheDocument()
    })

    const simButtons = screen.getAllByText('Simulate This Intervention')
    fireEvent.click(simButtons[0])

    expect(handleSimulate).toHaveBeenCalledWith('Atmospheric Gas Testing')
  })

  it('handles human review approval decision state transitions', async () => {
    render(<CorrectiveActionPanel analysis={mockAnalysis} />)

    await waitFor(() => {
      expect(screen.getAllByText('Approve Action')[0]).toBeInTheDocument()
    })

    const approveButtons = screen.getAllByText('Approve Action')
    fireEvent.click(approveButtons[0])

    expect(screen.getByText('✓ Approved Action')).toBeInTheDocument()
  })

  it('renders the cumulative prevention defense-in-depth matrix', async () => {
    render(<CorrectiveActionPanel analysis={mockAnalysis} />)

    await waitFor(() => {
      expect(
        screen.getByText('Multi-Barrier Cumulative Prevention Matrix')
      ).toBeInTheDocument()
    })

    expect(
      screen.getByText('Sequential Barrier Restoration Trajectory')
    ).toBeInTheDocument()
    expect(
      screen.getByText('Model Assumptions & Governance Criteria')
    ).toBeInTheDocument()
  })

  it('handles human review rejection decision', async () => {
    render(<CorrectiveActionPanel analysis={mockAnalysis} />)

    await waitFor(() => {
      expect(screen.getAllByText('Reject')[0]).toBeInTheDocument()
    })

    const rejectButtons = screen.getAllByText('Reject')
    fireEvent.click(rejectButtons[0])

    await waitFor(() => {
      expect(screen.getByText('✕ Rejected Action')).toBeInTheDocument()
    })
  })

  it('allows resetting decision back to pending review', async () => {
    render(<CorrectiveActionPanel analysis={mockAnalysis} />)

    await waitFor(() => {
      expect(screen.getAllByText('Approve Action')[0]).toBeInTheDocument()
    })

    fireEvent.click(screen.getAllByText('Approve Action')[0])
    await waitFor(() => {
      expect(screen.getByText('✓ Approved Action')).toBeInTheDocument()
    })

    const resetBtn = screen.getByTitle('Reset decision')
    fireEvent.click(resetBtn)

    await waitFor(() => {
      expect(screen.queryByText('✓ Approved Action')).not.toBeInTheDocument()
      expect(screen.getAllByText('Approve Action')[0]).toBeInTheDocument()
    })
  })

  it('filters by Engineering Controls', async () => {
    render(<CorrectiveActionPanel analysis={mockAnalysis} />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Engineering/i })).toBeInTheDocument()
    })

    const engBtn = screen.getByRole('button', { name: /Engineering/i })
    fireEvent.click(engBtn)

    await waitFor(() => {
      expect(engBtn.className).toContain('border-cyan-500/40')
    })
  })

  it('filters by Administrative Controls', async () => {
    render(<CorrectiveActionPanel analysis={mockAnalysis} />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Administrative/i })).toBeInTheDocument()
    })

    const adminBtn = screen.getByRole('button', { name: /Administrative/i })
    fireEvent.click(adminBtn)

    await waitFor(() => {
      expect(adminBtn.className).toContain('border-cyan-500/40')
    })
  })

  it('displays deterministic rule IDs on intervention cards', async () => {
    render(<CorrectiveActionPanel analysis={mockAnalysis} />)

    await waitFor(() => {
      expect(screen.getAllByText(/Rule:/i)[0]).toBeInTheDocument()
    })
  })

  it('displays baseline risk and predicted delta risk', async () => {
    render(<CorrectiveActionPanel analysis={mockAnalysis} />)

    await waitFor(() => {
      expect(screen.getAllByText(/Predicted Delta:/i)[0]).toBeInTheDocument()
    })
    expect(screen.getAllByText(/pts/i)[0]).toBeInTheDocument()
  })

  it('displays target barrier and observed state', async () => {
    render(<CorrectiveActionPanel analysis={mockAnalysis} />)

    await waitFor(() => {
      expect(screen.getAllByText(/Target Barrier:/i)[0]).toBeInTheDocument()
      expect(screen.getAllByText(/Observed State:/i)[0]).toBeInTheDocument()
    })
  })

  it('displays timeframe badges on action cards', async () => {
    render(<CorrectiveActionPanel analysis={mockAnalysis} />)

    await waitFor(() => {
      expect(screen.getAllByText(/Timeframe:/i)[0]).toBeInTheDocument()
    })
  })

  it('renders defense-in-depth sequential steps correctly in the matrix', async () => {
    render(<CorrectiveActionPanel analysis={mockAnalysis} />)

    await waitFor(
      () => {
        expect(
          screen.getAllByText(/Sequential Barrier Restoration Trajectory/i)[0]
        ).toBeInTheDocument()
      },
      { timeout: 4000 }
    )
  })

  it('handles empty analysis gracefully without crashing', async () => {
    const emptyAnalysis: AnalysisResponse = {
      ...mockAnalysis,
      safety_graph: { nodes: [], edges: [], causal_chains: [] },
    }
    render(<CorrectiveActionPanel analysis={emptyAnalysis} />)
    await waitFor(() => {
      expect(
        screen.getByText(/Automated Corrective Intervention Intelligence/i)
      ).toBeInTheDocument()
    })
  })
})


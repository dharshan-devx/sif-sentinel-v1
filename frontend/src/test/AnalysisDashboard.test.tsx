import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AnalysisDashboard } from '../components/analysis/AnalysisDashboard'
import { IncidentInput, PRESET_SCENARIOS } from '../components/analysis/IncidentInput'
import { RiskScoreWidget } from '../components/analysis/RiskScoreWidget'

describe('AnalysisDashboard and Subsystems', () => {
  it('renders IncidentInput with preset scenario buttons', () => {
    const handleAnalyze = vi.fn()
    render(<IncidentInput onAnalyze={handleAnalyze} isLoading={false} />)

    expect(screen.getByText(/Incident Narrative Analysis/i)).toBeInTheDocument()
    expect(screen.getByText(/Confined Space - Gas Testing Omission/i)).toBeInTheDocument()
    expect(screen.getByText(/Working at Height - Compliant Tie-Off/i)).toBeInTheDocument()

    // Trigger a preset scenario
    const heightBtn = screen.getByText(/Working at Height - Compliant Tie-Off/i)
    fireEvent.click(heightBtn)
    expect(handleAnalyze).toHaveBeenCalledWith(PRESET_SCENARIOS[1].text)
  })

  it('renders RiskScoreWidget with correct risk and SIF level indicators', () => {
    render(
      <RiskScoreWidget
        sifPotential={true}
        sifLevel="PSIF"
        probability={0.96}
        lsr="Confined Space Entry"
        risk={{
          score: 88,
          priority: 'P1_CRITICAL',
          components: [{ name: 'Hazard Energy', score: 35, reason: 'Toxic atmosphere' }],
          version: 'v2.0',
        }}
      />
    )

    expect(screen.getByText(/POTENTIAL SIF/i)).toBeInTheDocument()
    expect(screen.getByText('88')).toBeInTheDocument()
    expect(screen.getByText('P1_CRITICAL')).toBeInTheDocument()
    expect(screen.getByText(/Confined Space Entry/i)).toBeInTheDocument()
  })

  it('renders AnalysisDashboard with initial analysis on mount', async () => {
    render(<AnalysisDashboard />)

    await waitFor(() => {
      expect(
        screen.getByText(/Corrective Actions & Prevention/i)
      ).toBeInTheDocument()
    })

    // Switch to Causal Safety Graph tab
    const causalTabBtn = screen.getByRole('button', { name: /Causal Safety Graph/i })
    fireEvent.click(causalTabBtn)

    await waitFor(() => {
      expect(
        screen.getByText(/Explainable Causal Safety Reasoning & Simulation Engine/i)
      ).toBeInTheDocument()
    })

    // Verify presence of causal graph components
    expect(screen.getByText(/Causal Reasoning Timeline/i)).toBeInTheDocument()
  })
})

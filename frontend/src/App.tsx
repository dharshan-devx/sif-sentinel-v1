import { useState } from 'react'
import { AnalysisDashboard } from './components/analysis/AnalysisDashboard'
import { Shield, BookOpen } from 'lucide-react'

export function App() {
  const [activeTab, setActiveTab] = useState<'analysis' | 'about'>('analysis')

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-600 shadow-md shadow-cyan-900/30 flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base font-extrabold tracking-tight text-white font-sans">
                  SIF SENTINEL
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  v1.0 (Phase 5C)
                </span>
              </div>
              <div className="text-[11px] text-slate-400">
                Oil & Gas Precursor Intelligence • SIH26165
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-slate-300 font-mono text-[11px]">Causal Reasoning Engine Active</span>
            </div>

            <nav className="flex items-center gap-1 bg-slate-900/90 border border-slate-800 p-1 rounded-xl">
              <button
                onClick={() => setActiveTab('analysis')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeTab === 'analysis'
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Causal Analysis
              </button>
              <button
                onClick={() => setActiveTab('about')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeTab === 'about'
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Ontology & Rules
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Workspace Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'analysis' ? (
          <AnalysisDashboard />
        ) : (
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-6 max-w-4xl mx-auto backdrop-blur-md">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-cyan-400" />
                Deterministic Causal Safety Architecture
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                How SIF Sentinel transforms raw HSE incident narratives into verifiable causal safety reasoning chains.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="font-bold text-cyan-300 uppercase tracking-wider text-[11px]">
                  1. Canonical Barrier Ontology
                </div>
                <p className="text-slate-300 leading-relaxed">
                  Every high-energy activity (Confined Space, Height, LOTO, Lifting, Hot Work) is mapped to its mandatory safety barrier according to IOGP 9 Life-Saving Rules.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="font-bold text-violet-300 uppercase tracking-wider text-[11px]">
                  2. Nine Control Statuses
                </div>
                <p className="text-slate-300 leading-relaxed">
                  Supports VERIFIED, NOT_VERIFIED, PERFORMED, NOT_PERFORMED, FAILED, BYPASSED, MISSING, EXPIRED, and UNKNOWN to distinguish explicit compliance from ambiguous reporting.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="font-bold text-amber-300 uppercase tracking-wider text-[11px]">
                  3. Temporal Sequencing
                </div>
                <p className="text-slate-300 leading-relaxed">
                  Detects dangerous sequence inversions (e.g., worker entry occurring before atmospheric gas testing).
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="font-bold text-emerald-300 uppercase tracking-wider text-[11px]">
                  4. Grounded Evidence
                </div>
                <p className="text-slate-300 leading-relaxed">
                  Every deduction links directly back to exact source text spans and character offsets, eliminating hallucinated claims.
                </p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 bg-slate-950/60 py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-wrap items-center justify-between gap-4 text-[11px] text-slate-500">
          <div>
            SIF Sentinel • SIH26165 Causal Safety Reasoning Engine • Phase 5C
          </div>
          <div className="flex items-center gap-4">
            <span>IOGP / Energy Institute Standard</span>
            <span>REST API /api/v1/analyze</span>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App

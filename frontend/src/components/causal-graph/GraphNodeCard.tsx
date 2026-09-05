import React from 'react'
import type { GraphNode, CounterfactualScenario } from '../../types/analysis'
import {
  Activity,
  Flame,
  Shield,
  AlertOctagon,
  FileText,
  ShieldAlert,
  ShieldCheck,
  HelpCircle,
  Sparkles,
} from 'lucide-react'

interface Props {
  node: GraphNode
  isSelected: boolean
  isHighlighted: boolean
  activeScenario?: CounterfactualScenario | null
  viewMode?: 'OBSERVED' | 'SIMULATED' | 'COMPARE'
  onClick: () => void
}

export const GraphNodeCard: React.FC<Props> = ({
  node,
  isSelected,
  isHighlighted,
  activeScenario,
  viewMode = 'OBSERVED',
  onClick,
}) => {
  const isSimulatedNode =
    activeScenario?.affected_nodes?.includes(node.id) ||
    node.properties?.is_simulated ||
    (node.type === 'CONTROL' && activeScenario?.target_control.toLowerCase() === node.label.toLowerCase())

  const getNodeStyle = (type: string, status?: string) => {
    switch (type) {
      case 'ACTIVITY':
        return {
          border: 'border-violet-500/50 hover:border-violet-400',
          bg: 'bg-violet-950/40 text-violet-200',
          badgeBg: 'bg-violet-500/20 text-violet-300 border-violet-500/30',
          icon: <Activity className="w-4 h-4 text-violet-400" />,
          accent: 'from-violet-500/20 to-transparent',
        }
      case 'HAZARD':
        return {
          border: 'border-amber-500/50 hover:border-amber-400',
          bg: 'bg-amber-950/40 text-amber-200',
          badgeBg: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
          icon: <Flame className="w-4 h-4 text-amber-400" />,
          accent: 'from-amber-500/20 to-transparent',
        }
      case 'CONTROL':
        return {
          border: isSimulatedNode && viewMode !== 'OBSERVED'
            ? 'border-emerald-400/80 ring-2 ring-emerald-500/40 shadow-emerald-950/60'
            : 'border-blue-500/50 hover:border-blue-400',
          bg: isSimulatedNode && viewMode !== 'OBSERVED'
            ? 'bg-emerald-950/40 text-emerald-100'
            : 'bg-blue-950/40 text-blue-200',
          badgeBg: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
          icon: <Shield className="w-4 h-4 text-blue-400" />,
          accent: isSimulatedNode && viewMode !== 'OBSERVED'
            ? 'from-emerald-500/40 to-transparent'
            : 'from-blue-500/20 to-transparent',
        }
      case 'STATUS': {
        const isFail =
          status === 'NOT_VERIFIED' ||
          status === 'NOT_PERFORMED' ||
          status === 'FAILED' ||
          status === 'BYPASSED' ||
          status === 'MISSING' ||
          status === 'EXPIRED'
        const isOk = status === 'VERIFIED' || status === 'PERFORMED'

        if (isSimulatedNode && viewMode !== 'OBSERVED') {
          return {
            border: 'border-emerald-400/80 ring-2 ring-emerald-500/40 shadow-emerald-950/60',
            bg: 'bg-emerald-950/50 text-emerald-200',
            badgeBg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
            icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />,
            accent: 'from-emerald-500/40 to-transparent',
          }
        }

        if (isFail) {
          return {
            border: 'border-red-500/60 hover:border-red-400 shadow-red-950/50',
            bg: 'bg-red-950/50 text-red-200',
            badgeBg: 'bg-red-500/20 text-red-300 border-red-500/40',
            icon: <ShieldAlert className="w-4 h-4 text-red-400 animate-pulse" />,
            accent: 'from-red-500/30 to-transparent',
          }
        }
        if (isOk) {
          return {
            border: 'border-emerald-500/50 hover:border-emerald-400',
            bg: 'bg-emerald-950/40 text-emerald-200',
            badgeBg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
            icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />,
            accent: 'from-emerald-500/20 to-transparent',
          }
        }
        return {
          border: 'border-amber-500/50 hover:border-amber-400',
          bg: 'bg-amber-950/40 text-amber-200',
          badgeBg: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
          icon: <HelpCircle className="w-4 h-4 text-amber-400" />,
          accent: 'from-amber-500/20 to-transparent',
        }
      }
      case 'EXPOSURE':
      case 'PRECURSOR':
        if (isSimulatedNode && viewMode !== 'OBSERVED') {
          return {
            border: 'border-emerald-500/60 hover:border-emerald-400',
            bg: 'bg-emerald-950/40 text-emerald-200',
            badgeBg: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
            icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />,
            accent: 'from-emerald-500/20 to-transparent',
          }
        }
        return {
          border: 'border-rose-500/50 hover:border-rose-400',
          bg: 'bg-rose-950/40 text-rose-200',
          badgeBg: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
          icon: <AlertOctagon className="w-4 h-4 text-rose-400" />,
          accent: 'from-rose-500/20 to-transparent',
        }
      default:
        return {
          border: 'border-slate-700 hover:border-slate-600',
          bg: 'bg-slate-900/90 text-slate-200',
          badgeBg: 'bg-slate-800 text-slate-400 border-slate-700',
          icon: <FileText className="w-4 h-4 text-slate-400" />,
          accent: 'from-slate-700/20 to-transparent',
        }
    }
  }

  const effectiveStatus =
    isSimulatedNode && viewMode !== 'OBSERVED' && node.type === 'STATUS'
      ? activeScenario?.simulated_status
      : (typeof node.status === 'string' ? node.status : undefined)

  const style = getNodeStyle(node.type, effectiveStatus)

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onClick()
        }
      }}
      className={`group relative w-48 sm:w-56 p-3 rounded-xl border transition-all duration-200 cursor-pointer shadow-md backdrop-blur-sm select-none ${
        style.border
      } ${style.bg} ${
        isSelected
          ? 'ring-2 ring-cyan-400 shadow-cyan-500/20 scale-[1.02]'
          : isHighlighted
          ? 'ring-1 ring-white/40'
          : 'opacity-90 hover:opacity-100 hover:scale-[1.01]'
      } ${isSimulatedNode && viewMode !== 'OBSERVED' ? 'border-dashed' : ''}`}
    >
      {/* Subtle top gradient line */}
      <div
        className={`absolute inset-x-0 top-0 h-1 rounded-t-xl bg-gradient-to-r ${style.accent}`}
      />

      <div className="flex items-center justify-between gap-1 mb-2">
        <div className="flex items-center gap-1.5">
          {style.icon}
          <span className="text-[10px] font-mono uppercase tracking-wider font-bold text-slate-300">
            {node.type}
          </span>
        </div>

        {isSimulatedNode && viewMode !== 'OBSERVED' ? (
          <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 flex items-center gap-0.5">
            <Sparkles className="w-2.5 h-2.5" /> SIM
          </span>
        ) : node.confidence !== undefined ? (
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-black/40 text-slate-300 border border-white/5">
            {(node.confidence * 100).toFixed(0)}%
          </span>
        ) : null}
      </div>

      <div className="text-xs font-semibold text-white group-hover:text-cyan-200 transition-colors line-clamp-2 min-h-[32px]">
        {node.label}
      </div>

      {(node.status || effectiveStatus) && (
        <div className="mt-2 pt-2 border-t border-white/10 flex items-center justify-between">
          <span className="text-[9px] text-slate-400 uppercase font-mono">
            {isSimulatedNode && viewMode === 'COMPARE' ? 'Compare' : 'State'}
          </span>
          <span
            className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${style.badgeBg}`}
          >
            {isSimulatedNode && viewMode === 'COMPARE' && node.type === 'STATUS' ? (
              <span>
                <span className="line-through text-red-400 mr-1">{node.status}</span>
                <span className="text-emerald-300">→ {activeScenario?.simulated_status}</span>
              </span>
            ) : (
              effectiveStatus || node.status
            )}
          </span>
        </div>
      )}
    </div>
  )
}

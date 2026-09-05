import React, { useRef, useMemo, useState } from 'react'
import type { GraphNode, GraphEdge, CounterfactualScenario } from '../../types/analysis'
import { GraphNodeCard } from './GraphNodeCard'

interface Props {
  nodes: GraphNode[]
  edges?: GraphEdge[]
  selectedNodeId: string | null
  activeChainIdx?: number
  filterMode: string
  zoomLevel: number
  panOffset: { x: number; y: number }
  activeScenario?: CounterfactualScenario | null
  viewMode?: 'OBSERVED' | 'SIMULATED' | 'COMPARE'
  onSelectNode: (nodeId: string) => void
  onPanChange: (offset: { x: number; y: number }) => void
}

export const GraphCanvas: React.FC<Props> = ({
  nodes,
  selectedNodeId,
  filterMode,
  zoomLevel,
  panOffset,
  activeScenario,
  viewMode = 'OBSERVED',
  onSelectNode,
  onPanChange,
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })

  // Organize nodes by columnar stages
  const columns = useMemo(() => {
    const stageOrder: Array<GraphNode['type']> = [
      'ACTIVITY',
      'HAZARD',
      'CONTROL',
      'STATUS',
      'EXPOSURE',
      'PRECURSOR',
    ]

    const map = new Map<string, GraphNode[]>()
    stageOrder.forEach((st) => map.set(st, []))

    // If SIMULATED mode, use nodes from simulated_graph if available
    const activeNodes =
      viewMode === 'SIMULATED' && activeScenario?.simulated_graph?.nodes
        ? activeScenario.simulated_graph.nodes
        : nodes

    activeNodes.forEach((node) => {
      // Apply filters if any
      if (filterMode === 'FAILURES') {
        const isStatusFail =
          node.type === 'STATUS' &&
          (node.status === 'NOT_VERIFIED' ||
            node.status === 'NOT_PERFORMED' ||
            node.status === 'FAILED' ||
            node.status === 'BYPASSED' ||
            node.status === 'MISSING' ||
            node.status === 'EXPIRED')
        if (node.type === 'STATUS' && !isStatusFail) return
      } else if (filterMode === 'VERIFIED') {
        const isStatusOk =
          node.type === 'STATUS' && (node.status === 'VERIFIED' || node.status === 'PERFORMED')
        if (node.type === 'STATUS' && !isStatusOk) return
      }

      if (map.has(node.type)) {
        map.get(node.type)!.push(node)
      } else {
        if (!map.has('OTHER')) map.set('OTHER', [])
        map.get('OTHER')!.push(node)
      }
    })

    return Array.from(map.entries()).filter(([_, group]) => group.length > 0)
  }, [nodes, filterMode, viewMode, activeScenario])

  // Mouse pan handling
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return // only main mouse button
    setIsDragging(true)
    setDragStart({ x: e.clientX - panOffset.x, y: e.clientY - panOffset.y })
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return
    onPanChange({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    })
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  return (
    <div
      ref={containerRef}
      role="region"
      aria-label="Causal Safety DAG Canvas"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      className={`relative w-full h-[480px] rounded-xl bg-slate-950/90 border border-slate-800 overflow-hidden select-none cursor-grab ${
        isDragging ? 'cursor-grabbing' : ''
      }`}
    >
      {/* Background Grid Pattern */}
      <div
        className="absolute inset-0 opacity-20 pointer-events-none"
        style={{
          backgroundImage:
            'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.15) 1px, transparent 0)',
          backgroundSize: '24px 24px',
        }}
      />

      {/* Transform Container (Zoom + Pan) */}
      <div
        className="absolute inset-0 p-8 transition-transform duration-75 origin-center flex items-center justify-start min-w-max gap-8 sm:gap-12"
        style={{
          transform: `translate(${panOffset.x}px, ${panOffset.y}px) scale(${zoomLevel})`,
        }}
      >
        {columns.map(([type, groupNodes], colIdx) => (
          <div key={type} className="flex flex-col items-center gap-4 shrink-0 relative">
            <div className="text-[10px] font-mono font-bold uppercase tracking-widest px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-400">
              Stage {colIdx + 1}: {type}
            </div>

            <div className="flex flex-col gap-4">
              {groupNodes.map((node) => (
                <GraphNodeCard
                  key={node.id}
                  node={node}
                  isSelected={selectedNodeId === node.id}
                  isHighlighted={selectedNodeId === null || selectedNodeId === node.id}
                  activeScenario={activeScenario}
                  viewMode={viewMode}
                  onClick={() => onSelectNode(node.id)}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

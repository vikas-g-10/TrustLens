import React, { useState } from 'react';
import { 
  Network, 
  Info, 
  ArrowRight,
  ShieldAlert,
  Layers,
  Sparkles,
  GitBranch
} from 'lucide-react';
import { GraphNode, GraphEdge } from '../types/investigation';

interface EvidenceGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export const EvidenceGraph: React.FC<EvidenceGraphProps> = ({ nodes, edges }) => {
  const [selectedNodeId, setSelectedNodeId] = useState<string>(
    () => (nodes.some(n => n.id === 'CONTRADICTION') ? 'CONTRADICTION' : nodes[nodes.length - 1]?.id ?? '')
  );

  // Exact 9-node layout on a large, high-visibility 960x560 canvas
  const nodeLayout: Record<string, { x: number; y: number; category: string }> = {
    CLAIM: { x: 480, y: 55, category: 'claim' },
    MEDIA: { x: 190, y: 180, category: 'media' },
    URL: { x: 380, y: 180, category: 'url' },
    SUPPORTING_SOURCE_A: { x: 620, y: 180, category: 'source' },
    SUPPORTING_SOURCE_B: { x: 820, y: 180, category: 'source' },
    EARLIER_PUBLICATION: { x: 190, y: 335, category: 'counter' },
    CONTRADICTION: { x: 410, y: 360, category: 'conflict' },
    COUNTER_EVIDENCE: { x: 670, y: 360, category: 'counter' },
    FINAL_ASSESSMENT: { x: 480, y: 500, category: 'verdict' },
  };

  const selectedNode = nodes.find(n => n.id === selectedNodeId) || nodes[0];

  const getNodeStyling = (nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId);
    if (node && !nodeLayout[nodeId]) {
      // Generic (live) nodes: style by category/status using the existing presets
      const preset: Record<string, string> = { claim: 'CLAIM', media: 'MEDIA', url: 'URL', verdict: 'FINAL_ASSESSMENT' };
      if (preset[node.category]) nodeId = preset[node.category];
      else if (node.status === 'supporting') nodeId = 'SUPPORTING_SOURCE_A';
      else if (node.status === 'challenging') nodeId = 'CONTRADICTION';
    }
    switch (nodeId) {
      case 'CLAIM':
        return {
          fill: '#083344',
          stroke: '#06B6D4',
          textFill: '#67E8F9',
          border: 'border-cyan-500',
          badgeText: 'Primary Proposition',
          badgeColor: 'text-cyan-400 bg-cyan-950/60 border-cyan-500/40'
        };
      case 'MEDIA':
        return {
          fill: '#0F172A',
          stroke: '#38BDF8',
          textFill: '#BAE6FD',
          border: 'border-sky-500',
          badgeText: 'Optical Forensics',
          badgeColor: 'text-sky-400 bg-sky-950/60 border-sky-500/40'
        };
      case 'URL':
        return {
          fill: '#2A080C',
          stroke: '#EF4444',
          textFill: '#FCA5A5',
          border: 'border-red-500',
          badgeText: 'Dissemination Vector',
          badgeColor: 'text-red-400 bg-red-950/60 border-red-500/40'
        };
      case 'SUPPORTING_SOURCE_A':
      case 'SUPPORTING_SOURCE_B':
        return {
          fill: '#022C22',
          stroke: '#10B981',
          textFill: '#6EE7B7',
          border: 'border-emerald-500',
          badgeText: 'Supporting Corroboration',
          badgeColor: 'text-emerald-400 bg-emerald-950/60 border-emerald-500/40'
        };
      case 'EARLIER_PUBLICATION':
        return {
          fill: '#270810',
          stroke: '#F43F5E',
          textFill: '#FDA4AF',
          border: 'border-rose-500',
          badgeText: 'Archival Record (2022)',
          badgeColor: 'text-rose-400 bg-rose-950/60 border-rose-500/40'
        };
      case 'CONTRADICTION':
        return {
          fill: '#350A10',
          stroke: '#EF4444',
          textFill: '#FCA5A5',
          border: 'border-red-500',
          badgeText: 'Conflict Node',
          badgeColor: 'text-red-400 bg-red-950/60 border-red-500/40'
        };
      case 'COUNTER_EVIDENCE':
        return {
          fill: '#381A05',
          stroke: '#F97316',
          textFill: '#FDBA74',
          border: 'border-orange-500',
          badgeText: 'Refuting Counter-Evidence',
          badgeColor: 'text-orange-400 bg-orange-950/60 border-orange-500/40'
        };
      case 'FINAL_ASSESSMENT':
        return {
          fill: '#3B2404',
          stroke: '#EAB308',
          textFill: '#FEF08A',
          border: 'border-yellow-500',
          badgeText: 'Synthesized Verdict',
          badgeColor: 'text-yellow-400 bg-yellow-950/60 border-yellow-500/40'
        };
      default:
        return {
          fill: '#1E293B',
          stroke: '#64748B',
          textFill: '#E2E8F0',
          border: 'border-slate-500',
          badgeText: 'Evidence Node',
          badgeColor: 'text-slate-400 bg-slate-900 border-slate-700'
        };
    }
  };

  return (
    <div id="evidence-graph" className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 sm:p-8 backdrop-blur-xl shadow-2xl space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-950/40 border border-cyan-500/30 text-cyan-400">
              <Network className="h-4 w-4" />
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-white font-display">
              EVIDENCE GRAPH
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1 font-sans">
            Interactive directed evidence network displaying how corroborations and archival conflicts synthesize into reasoning.
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center flex-wrap gap-3 text-xs font-mono bg-slate-950 px-3.5 py-2 rounded-lg border border-slate-800">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 inline-block" />
            <span className="text-emerald-400">Supporting</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-red-500 inline-block" />
            <span className="text-red-400">Contradicting</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-yellow-400 inline-block" />
            <span className="text-yellow-400">Final Assessment</span>
          </div>
        </div>
      </div>

      {/* Prominent Key Differentiator Statement (Requirement 7) */}
      <div className="rounded-xl border border-cyan-500/40 bg-gradient-to-r from-cyan-950/40 via-slate-950 to-slate-950 p-4 sm:p-5 flex items-start gap-3.5">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-cyan-500/20 border border-cyan-400/40 text-cyan-300">
          <GitBranch className="h-5 w-5" />
        </div>
        <div>
          <div className="text-base sm:text-lg font-bold text-cyan-300 font-display">
            “3 sources ≠ 3 independent confirmations.”
          </div>
          <p className="text-xs sm:text-sm text-slate-300 font-sans mt-0.5">
            TrustLens analyzes evidence independence before increasing confidence.
          </p>
        </div>
      </div>

      {/* Main Graph Grid (Large SVG + Node Inspector) */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        
        {/* Left/Center SVG Canvas */}
        <div className="xl:col-span-8 rounded-xl border border-slate-800 bg-[#040813] p-3 relative overflow-hidden">
          {/* Subtle grid background */}
          <div className="absolute inset-0 forensic-grid opacity-35 pointer-events-none" />

          {/* SVG Canvas */}
          <svg
            viewBox="0 0 960 560"
            className="w-full h-auto select-none"
            style={{ minHeight: '480px' }}
          >
            <defs>
              {/* Arrow Marker Definitions */}
              <marker
                id="marker-green"
                viewBox="0 0 10 10"
                refX="26"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#10B981" />
              </marker>

              <marker
                id="marker-red"
                viewBox="0 0 10 10"
                refX="26"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#EF4444" />
              </marker>

              <marker
                id="marker-yellow"
                viewBox="0 0 10 10"
                refX="26"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#EAB308" />
              </marker>

              <marker
                id="marker-neutral"
                viewBox="0 0 10 10"
                refX="26"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#38BDF8" />
              </marker>

              {/* Glow filter */}
              <filter id="node-glow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="0" stdDeviation="5" floodColor="#06B6D4" floodOpacity="0.4" />
              </filter>
            </defs>

            {/* Edge Connections */}
            {edges.map((edge, idx) => {
              const startNode = nodes.find(n => n.id === edge.from);
              const endNode = nodes.find(n => n.id === edge.to);
              const start = nodeLayout[edge.from] ?? startNode;
              const end = nodeLayout[edge.to] ?? endNode;
              if (!start || !end) return null;

              const isConnectedToSelected =
                edge.from === selectedNodeId || edge.to === selectedNodeId;

              let strokeColor = '#38BDF8';
              let markerEnd = 'url(#marker-neutral)';
              let strokeDash = 'none';

              if (edge.type === 'supporting') {
                strokeColor = '#10B981'; // Green
                markerEnd = 'url(#marker-green)';
              } else if (edge.type === 'contradicting') {
                strokeColor = '#EF4444'; // Red/Orange
                markerEnd = 'url(#marker-red)';
                strokeDash = '6,4';
              } else if (edge.type === 'final') {
                strokeColor = '#EAB308'; // Yellow
                markerEnd = 'url(#marker-yellow)';
              }

              // Curved Bezier
              const midY = (start.y + end.y) / 2;
              const pathD = `M ${start.x} ${start.y} C ${start.x} ${midY}, ${end.x} ${midY}, ${end.x} ${end.y}`;

              return (
                <g key={idx}>
                  <path
                    d={pathD}
                    fill="none"
                    stroke={strokeColor}
                    strokeWidth={isConnectedToSelected ? 3 : 2}
                    strokeDasharray={strokeDash}
                    markerEnd={markerEnd}
                    opacity={isConnectedToSelected ? 1 : 0.75}
                    className="transition-all duration-300"
                  />
                  {/* Flowing animated pulse dashes */}
                  <path
                    d={pathD}
                    fill="none"
                    stroke={strokeColor}
                    strokeWidth={isConnectedToSelected ? 3.5 : 2}
                    strokeDasharray="4 12"
                    className="animate-scanline"
                    opacity="0.9"
                  />
                </g>
              );
            })}

            {/* Node Items */}
            {nodes.map((node) => {
              const pos = nodeLayout[node.id] ?? { x: node.x, y: node.y };
              if (!pos) return null;

              const isSelected = node.id === selectedNodeId;
              const style = getNodeStyling(node.id);

              return (
                <g
                  key={node.id}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  onClick={() => setSelectedNodeId(node.id)}
                  className="cursor-pointer group"
                >
                  {/* Outer selection ring */}
                  {isSelected && (
                    <circle
                      r="36"
                      fill="none"
                      stroke={style.stroke}
                      strokeWidth="2"
                      strokeDasharray="4 4"
                      className="animate-spin"
                      style={{ animationDuration: '9s' }}
                    />
                  )}

                  {/* Main Node Body */}
                  <rect
                    x="-75"
                    y="-24"
                    width="150"
                    height="48"
                    rx="10"
                    fill={style.fill}
                    stroke={isSelected ? '#FFFFFF' : style.stroke}
                    strokeWidth={isSelected ? 2.5 : 1.5}
                    className="transition-all duration-200 group-hover:scale-105"
                  />

                  {/* Node Label Text */}
                  <text
                    x="0"
                    y="-3"
                    textAnchor="middle"
                    fill={style.textFill}
                    fontSize="10"
                    fontFamily="JetBrains Mono, monospace"
                    fontWeight="bold"
                    letterSpacing="0.04em"
                  >
                    {node.label}
                  </text>

                  {/* Subtext description pill */}
                  {node.sublabel && (
                    <text
                      x="0"
                      y="14"
                      textAnchor="middle"
                      fill="#94A3B8"
                      fontSize="9"
                      fontFamily="Plus Jakarta Sans, sans-serif"
                    >
                      {node.sublabel}
                    </text>
                  )}

                  {/* Colored status dot */}
                  <circle
                    cx="-60"
                    cy="0"
                    r="4"
                    fill={style.stroke}
                  />
                </g>
              );
            })}
          </svg>

          {/* Interactive Hint */}
          <div className="absolute bottom-3 left-3 bg-slate-950/90 px-3 py-1.5 rounded-lg border border-slate-800 text-[11px] font-mono text-slate-300 flex items-center gap-2">
            <Info className="h-3.5 w-3.5 text-cyan-400" />
            <span>Click any node to inspect evidence vectors and connections</span>
          </div>
        </div>

        {/* Right Node Inspector (XL: 4 cols) */}
        <div className="xl:col-span-4 rounded-xl border border-slate-800 bg-[#060B16] p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400 font-bold">
              NODE INSPECTOR
            </span>
            <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${getNodeStyling(selectedNode.id).badgeColor}`}>
              {getNodeStyling(selectedNode.id).badgeText}
            </span>
          </div>

          <div>
            <span className="text-[11px] font-mono text-cyan-400">Node Identifier:</span>
            <h3 className="text-lg font-bold text-white font-mono mt-0.5">
              {selectedNode.label}
            </h3>
            <p className="text-xs text-slate-200 mt-2 leading-relaxed">
              {selectedNode.description}
            </p>
          </div>

          {/* Connected Relations */}
          <div className="space-y-2 pt-2 border-t border-slate-800">
            <span className="text-[11px] font-mono text-slate-400 block font-bold">
              Directed Graph Links:
            </span>

            <div className="space-y-1.5 font-mono text-xs">
              {edges
                .filter(e => e.from === selectedNode.id || e.to === selectedNode.id)
                .map((e, idx) => {
                  const isOutgoing = e.from === selectedNode.id;
                  const partner = isOutgoing ? e.to : e.from;
                  const isSupporting = e.type === 'supporting';
                  const isContradicting = e.type === 'contradicting';
                  const isFinal = e.type === 'final';

                  return (
                    <div 
                      key={idx}
                      className="rounded bg-slate-900/90 p-2.5 border border-slate-800 text-[11px] flex items-center justify-between"
                    >
                      <div className="flex items-center gap-1.5">
                        <span className={isOutgoing ? 'text-cyan-400' : 'text-slate-400'}>
                          {isOutgoing ? '→ To:' : '← From:'}
                        </span>
                        <strong className="text-slate-200 truncate max-w-[120px]">{partner}</strong>
                      </div>
                      <span className={
                        isSupporting 
                          ? 'text-emerald-400 font-bold' 
                          : isContradicting 
                          ? 'text-red-400 font-bold' 
                          : isFinal
                          ? 'text-yellow-400 font-bold'
                          : 'text-slate-400'
                      }>
                        {e.label || (isSupporting ? 'Supports' : isContradicting ? 'Conflicts' : 'Derives')}
                      </span>
                    </div>
                  );
                })}
            </div>
          </div>

          {/* Epistemic Diagnostic Note */}
          <div className="rounded-lg border border-slate-800 bg-slate-950 p-3.5 text-xs font-sans text-slate-300">
            <strong className="text-slate-100 block mb-1 font-mono text-[11px]">
              Evidentiary Significance:
            </strong>
            {selectedNode.significance ? (
              <p className="text-slate-300 leading-relaxed">{selectedNode.significance}</p>
            ) : selectedNode.id === 'CONTRADICTION' ? (
              <p className="text-red-300 leading-relaxed">
                Primary contradiction anchor: Historical archival matching invalidates the claim that this video represents today's Bengaluru flood.
              </p>
            ) : selectedNode.id === 'EARLIER_PUBLICATION' ? (
              <p className="text-rose-300 leading-relaxed">
                Archival match from August 2022 proves the physical video existed years prior to today's claimed event.
              </p>
            ) : selectedNode.id === 'COUNTER_EVIDENCE' ? (
              <p className="text-orange-300 leading-relaxed">
                Direct counter-evidence invalidates temporal claims even though rain actually occurred in Bengaluru today.
              </p>
            ) : selectedNode.id === 'FINAL_ASSESSMENT' ? (
              <p className="text-amber-300 leading-relaxed">
                Synthesizes the standoff: Authentic footage reused out of context yields an INCONCLUSIVE assessment (78% confidence).
              </p>
            ) : (
              <p className="text-slate-400 leading-relaxed">
                Structural node ingested by the automated digital evidence extraction engine.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

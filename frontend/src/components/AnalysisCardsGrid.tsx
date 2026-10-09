import React, { useState } from 'react';
import { 
  Check, 
  AlertTriangle, 
  AlertOctagon, 
  ChevronDown, 
  ChevronUp, 
  ExternalLink,
  Shield, 
  Video, 
  Link as LinkIcon, 
  Layers, 
  GitCompare, 
  Network, 
  Search
} from 'lucide-react';
import { AnalysisCardData } from '../types/investigation';

interface AnalysisCardsGridProps {
  cards: AnalysisCardData[];
  submittedUrl: string;
  isDemo: boolean;
  onInspectMedia?: () => void;
}

export const AnalysisCardsGrid: React.FC<AnalysisCardsGridProps> = ({ 
  cards,
  submittedUrl,
  isDemo,
  onInspectMedia 
}) => {
  const [expandedCardId, setExpandedCardId] = useState<string | null>(null);

  const toggleExpand = (cardId: string) => {
    setExpandedCardId(prev => prev === cardId ? null : cardId);
  };

  const getCardIcon = (id: string) => {
    switch (id) {
      case 'media_forensics': return <Video className="h-4 w-4" />;
      case 'url_security': return <LinkIcon className="h-4 w-4" />;
      case 'independent_evidence': return <Layers className="h-4 w-4" />;
      case 'contradiction_detection': return <GitCompare className="h-4 w-4" />;
      case 'source_independence': return <Network className="h-4 w-4" />;
      case 'counter_evidence': return <Search className="h-4 w-4" />;
      default: return <Shield className="h-4 w-4" />;
    }
  };

  const renderBadge = (badge: AnalysisCardData['badge']) => {
    const colorClasses = {
      amber: 'border-amber-500/40 bg-amber-500/10 text-amber-300',
      red: 'border-red-500/40 bg-red-500/10 text-red-300',
      green: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300',
      orange: 'border-orange-500/40 bg-orange-500/10 text-orange-300',
      cyan: 'border-cyan-500/40 bg-cyan-500/10 text-cyan-300',
      slate: 'border-slate-600/60 bg-slate-700/20 text-slate-300'
    }[badge.variant];

    return (
      <span className={`inline-flex items-center gap-1 rounded-md border px-2.5 py-0.5 text-xs font-mono font-bold tracking-wide ${colorClasses}`}>
        {badge.text}
      </span>
    );
  };

  const renderItemIcon = (type: 'check' | 'warning' | 'alert' | 'info') => {
    switch (type) {
      case 'check':
        return <Check className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />;
      case 'warning':
        return <AlertTriangle className="h-3.5 w-3.5 text-amber-400 shrink-0 mt-0.5" />;
      case 'alert':
        return <AlertOctagon className="h-3.5 w-3.5 text-red-400 shrink-0 mt-0.5" />;
      case 'info':
        return <Shield className="h-3.5 w-3.5 text-cyan-400 shrink-0 mt-0.5" />;
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white font-display">
            Six-Pillar Evidence Analysis
          </h2>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Click any card to inspect findings. Pillars without real data are marked Unavailable.
          </p>
        </div>
        <span className="text-xs font-mono text-cyan-400 hidden sm:inline-block">
          Interactive Inspection Mode
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards.map((card) => {
          const isExpanded = expandedCardId === card.id;

          return (
            <div
              key={card.id}
              className={`rounded-xl border transition-all duration-200 overflow-hidden flex flex-col justify-between ${
                isExpanded
                  ? 'border-cyan-500/50 bg-slate-900 shadow-xl'
                  : 'border-slate-800 bg-slate-900/70 hover:border-slate-700 hover:bg-slate-900/90'
              }`}
            >
              {/* Card Header */}
              <div 
                onClick={() => toggleExpand(card.id)}
                className="p-4 sm:p-5 cursor-pointer select-none space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs font-bold tracking-wider">
                    {getCardIcon(card.id)}
                    <span>{card.title}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {isDemo && (
                      <span className="text-[9px] font-mono font-semibold bg-slate-800 text-amber-300 px-1.5 py-0.5 rounded border border-amber-500/30">
                        SIMULATED ANALYSIS
                      </span>
                    )}
                    {renderBadge(card.badge)}
                  </div>
                </div>

                {card.id === 'url_security' && (
                  <div className="rounded bg-slate-950/80 p-2 border border-slate-800 text-[11px] font-mono space-y-0.5">
                    <span className="text-[10px] text-slate-400 block">Submitted:</span>
                    <span className="text-cyan-300 truncate block">{submittedUrl}</span>
                  </div>
                )}

                {/* Bullet Points */}
                <div className="space-y-2 pt-1">
                  {card.summaryItems.map((item, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-xs">
                      {renderItemIcon(item.iconType)}
                      <span className={
                        item.variant === 'red' 
                          ? 'text-red-300 font-medium' 
                          : item.variant === 'amber' 
                          ? 'text-amber-200' 
                          : item.variant === 'green'
                          ? 'text-emerald-200'
                          : 'text-slate-300'
                      }>
                        {item.text}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Expand / Collapse trigger */}
                <div className="flex items-center justify-between pt-2 text-[11px] font-mono text-slate-500 border-t border-slate-800/60">
                  <span>{isExpanded ? 'Collapse technical notes' : 'Click to inspect deeper'}</span>
                  {isExpanded ? (
                    <ChevronUp className="h-3.5 w-3.5 text-cyan-400" />
                  ) : (
                    <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
                  )}
                </div>
              </div>

              {/* Expandable Deep Forensic Inspection Drawer */}
              {isExpanded && (
                <div className="border-t border-slate-800 bg-[#060A14] p-4 text-xs space-y-3 font-sans animate-in fade-in duration-150">
                  <div>
                    <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400 block mb-1">
                      Forensic Findings
                    </span>
                    <p className="text-slate-300 text-xs leading-relaxed">
                      {card.details.overview}
                    </p>
                  </div>

                  {/* Quantitative Forensic Telemetry */}
                  {card.details.metrics && card.details.metrics.length > 0 && (
                    <div className="grid grid-cols-2 gap-2 pt-1 font-mono">
                      {card.details.metrics.map((m, mIdx) => (
                        <div key={mIdx} className="rounded bg-slate-900/80 p-2 border border-slate-800">
                          <span className="text-[10px] text-slate-400 block">{m.label}</span>
                          <span className="text-xs font-bold text-cyan-300">{m.value}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Forensic Observation Log */}
                  <div>
                    <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400 block mb-1">
                      Observation Log
                    </span>
                    <ul className="space-y-1 text-[11px] text-slate-400 list-disc list-inside">
                      {card.details.forensicNotes.map((note, nIdx) => (
                        <li key={nIdx}>{note}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Specific Disclaimer if URL or Media */}
                  {card.details.technicalDisclaimer && (
                    <div className="rounded border border-slate-800 bg-slate-900/60 p-2 text-[10px] text-slate-400 font-mono">
                      ⚠ {card.details.technicalDisclaimer}
                    </div>
                  )}

                  {isDemo && card.id === 'media_forensics' && onInspectMedia && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onInspectMedia();
                      }}
                      className="w-full mt-2 flex items-center justify-center gap-1.5 rounded bg-cyan-950/60 border border-cyan-500/40 py-1.5 text-xs font-mono font-semibold text-cyan-300 hover:bg-cyan-900/60 transition-colors"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                      <span>Launch Video Spectrogram HUD</span>
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

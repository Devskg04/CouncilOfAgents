import React from 'react';
import { Factor } from '../types/aether';
import { ChevronDown, ChevronUp, AlertTriangle, TrendingUp } from 'lucide-react';
import { DebateThread } from './DebateThread';
import { SynthesisPanel } from './SynthesisPanel';

interface FactorCardProps {
  factor: Factor;
  isExpanded: boolean;
  onToggle: () => void;
}

export function FactorCard({ factor, isExpanded, onToggle }: FactorCardProps) {
  const disagreementLevel = 
    factor.disagreementScore > 0.7 ? 'high' : 
    factor.disagreementScore > 0.4 ? 'medium' : 'low';

  const disagreementColors = {
    high: 'text-red-400 bg-red-500/20 border-red-500/30',
    medium: 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30',
    low: 'text-green-400 bg-green-500/20 border-green-500/30',
  };

  return (
    <div className="bg-slate-800/50 border border-cyan-500/30 rounded-lg backdrop-blur-sm overflow-hidden">
      {/* Factor Header */}
      <button
        onClick={onToggle}
        className="w-full p-6 flex items-center justify-between hover:bg-slate-800/70 transition-colors"
      >
        <div className="flex-1 text-left">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-xl text-cyan-300 font-semibold">{factor.name}</h3>
            <span className="text-sm text-slate-400">Weight: {(factor.weight * 100).toFixed(0)}%</span>
          </div>
          <p className="text-slate-400 text-sm">{factor.description}</p>
        </div>

        <div className="flex items-center gap-4 ml-4">
          {/* Disagreement Badge */}
          <div className={`px-3 py-1 rounded-full border text-xs font-semibold ${disagreementColors[disagreementLevel]}`}>
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-3 h-3" />
              Disagreement: {(factor.disagreementScore * 100).toFixed(0)}%
            </div>
          </div>

          {isExpanded ? (
            <ChevronUp className="w-6 h-6 text-cyan-400" />
          ) : (
            <ChevronDown className="w-6 h-6 text-cyan-400" />
          )}
        </div>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-slate-700 p-6 space-y-6">
          {/* Debate Thread */}
          <div>
            <h4 className="text-lg text-cyan-400 font-semibold mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Agent Debate (Multi-Round)
            </h4>
            <DebateThread messages={factor.debate} />
          </div>

          {/* Synthesis */}
          <SynthesisPanel synthesis={factor.synthesis} />
        </div>
      )}
    </div>
  );
}

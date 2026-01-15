import React from 'react';
import { TrendingUp, AlertTriangle, Target, Users } from 'lucide-react';

interface MetricsPanelProps {
  confidence: number;
  riskScore: number;
  disagreementScore: number;
  agentInfluence: Record<string, number>;
}

export function MetricsPanel({
  confidence,
  riskScore,
  disagreementScore,
  agentInfluence,
}: MetricsPanelProps) {
  const getScoreColor = (score: number, inverse: boolean = false) => {
    const threshold = inverse ? 1 - score : score;
    if (threshold > 0.7) return 'text-green-400';
    if (threshold > 0.4) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getScoreBg = (score: number, inverse: boolean = false) => {
    const threshold = inverse ? 1 - score : score;
    if (threshold > 0.7) return 'bg-green-500/20 border-green-500/30';
    if (threshold > 0.4) return 'bg-yellow-500/20 border-yellow-500/30';
    return 'bg-red-500/20 border-red-500/30';
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Confidence Score */}
      <div className={`${getScoreBg(confidence)} border rounded-lg p-6`}>
        <div className="flex items-center gap-3 mb-3">
          <Target className={`w-6 h-6 ${getScoreColor(confidence)}`} />
          <h3 className="text-slate-300 font-semibold">Confidence</h3>
        </div>
        <div className={`text-4xl font-bold ${getScoreColor(confidence)} mb-2`}>
          {(confidence * 100).toFixed(0)}%
        </div>
        <p className="text-slate-400 text-sm">
          System certainty in recommendation
        </p>
      </div>

      {/* Risk Score */}
      <div className={`${getScoreBg(riskScore, true)} border rounded-lg p-6`}>
        <div className="flex items-center gap-3 mb-3">
          <AlertTriangle className={`w-6 h-6 ${getScoreColor(riskScore, true)}`} />
          <h3 className="text-slate-300 font-semibold">Risk Level</h3>
        </div>
        <div className={`text-4xl font-bold ${getScoreColor(riskScore, true)} mb-2`}>
          {(riskScore * 100).toFixed(0)}%
        </div>
        <p className="text-slate-400 text-sm">
          Derived from debate conflict intensity
        </p>
      </div>

      {/* Disagreement Score */}
      <div className={`${getScoreBg(disagreementScore, true)} border rounded-lg p-6`}>
        <div className="flex items-center gap-3 mb-3">
          <Users className={`w-6 h-6 ${getScoreColor(disagreementScore, true)}`} />
          <h3 className="text-slate-300 font-semibold">Disagreement</h3>
        </div>
        <div className={`text-4xl font-bold ${getScoreColor(disagreementScore, true)} mb-2`}>
          {(disagreementScore * 100).toFixed(0)}%
        </div>
        <p className="text-slate-400 text-sm">
          Average agent debate divergence
        </p>
      </div>
    </div>
  );
}

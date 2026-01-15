import React from 'react';
import { Decision } from '../types/aether';
import { X, Clock, CheckCircle, XCircle, AlertCircle, FileText } from 'lucide-react';

interface DecisionHistoryProps {
  decisions: Decision[];
  onClose: () => void;
}

export function DecisionHistory({ decisions, onClose }: DecisionHistoryProps) {
  const getDecisionIcon = (decision: string) => {
    switch (decision) {
      case 'PROCEED':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'REJECT':
        return <XCircle className="w-5 h-5 text-red-400" />;
      case 'CONDITIONAL_PROCEED':
        return <AlertCircle className="w-5 h-5 text-yellow-400" />;
      default:
        return <FileText className="w-5 h-5 text-blue-400" />;
    }
  };

  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case 'PROCEED':
        return 'text-green-400';
      case 'REJECT':
        return 'text-red-400';
      case 'CONDITIONAL_PROCEED':
        return 'text-yellow-400';
      default:
        return 'text-blue-400';
    }
  };

  return (
    <div className="bg-slate-800/50 border border-cyan-500/30 rounded-lg backdrop-blur-sm">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-slate-700">
        <h2 className="text-2xl text-cyan-300 font-semibold">Decision History</h2>
        <button
          onClick={onClose}
          className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
        >
          <X className="w-6 h-6 text-slate-400" />
        </button>
      </div>

      {/* History List */}
      <div className="p-6">
        {decisions.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <p className="text-slate-400">No decisions in history yet</p>
          </div>
        ) : (
          <div className="space-y-4">
            {decisions.map((decision) => (
              <div
                key={decision.id}
                className="bg-slate-900/50 border border-slate-700 hover:border-cyan-500/30 rounded-lg p-5 transition-colors"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    {getDecisionIcon(decision.finalRecommendation.decision)}
                    <span className={`font-semibold ${getDecisionColor(decision.finalRecommendation.decision)}`}>
                      {decision.finalRecommendation.decision.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-500 text-sm">
                    <Clock className="w-4 h-4" />
                    {decision.timestamp.toLocaleDateString()}
                  </div>
                </div>

                <p className="text-slate-300 mb-3 line-clamp-2">
                  {decision.problemStatement}
                </p>

                <div className="flex items-center gap-6 text-sm">
                  <div>
                    <span className="text-slate-500">Factors: </span>
                    <span className="text-cyan-400">{decision.factors.length}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Confidence: </span>
                    <span className="text-cyan-400">
                      {(decision.finalRecommendation.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">Risk: </span>
                    <span className={decision.overallRiskScore > 0.6 ? 'text-red-400' : 'text-green-400'}>
                      {(decision.overallRiskScore * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                {decision.humanOverride && (
                  <div className="mt-3 pt-3 border-t border-slate-700">
                    <span className="text-xs text-orange-400">
                      ⚠️ Human override applied
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

import React from 'react';
import { FinalRecommendation } from '../types/aether';
import { Gavel, CheckCircle, XCircle, AlertCircle, TrendingUp } from 'lucide-react';

interface FinalDecisionPanelProps {
  recommendation: FinalRecommendation;
  timestamp: Date;
}

export function FinalDecisionPanel({ recommendation, timestamp }: FinalDecisionPanelProps) {
  const decisionConfig = {
    PROCEED: { color: 'text-green-400', bg: 'bg-green-500/20', border: 'border-green-500/30', label: 'PROCEED' },
    REJECT: { color: 'text-red-400', bg: 'bg-red-500/20', border: 'border-red-500/30', label: 'REJECT' },
    CONDITIONAL_PROCEED: { color: 'text-yellow-400', bg: 'bg-yellow-500/20', border: 'border-yellow-500/30', label: 'CONDITIONAL PROCEED' },
    NEEDS_MORE_DATA: { color: 'text-blue-400', bg: 'bg-blue-500/20', border: 'border-blue-500/30', label: 'NEEDS MORE DATA' },
  };

  const config = decisionConfig[recommendation.decision];

  return (
    <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 border-2 border-cyan-500/50 rounded-lg p-8 backdrop-blur-sm shadow-2xl shadow-cyan-500/10">
      {/* Header */}
      <div className="flex items-center justify-center gap-4 mb-6 pb-6 border-b border-slate-700">
        <Gavel className="w-10 h-10 text-cyan-400" />
        <h2 className="text-3xl text-cyan-300 font-bold">FINAL DECISION</h2>
      </div>

      {/* Decision Badge */}
      <div className={`${config.bg} ${config.border} border-2 rounded-lg p-6 mb-6`}>
        <div className="flex items-center justify-center gap-3 mb-3">
          <div className={`text-4xl font-bold ${config.color}`}>{config.label}</div>
        </div>
        <div className="flex justify-center gap-8 mt-4">
          <div className="text-center">
            <p className="text-slate-400 text-sm mb-1">Confidence</p>
            <p className={`text-2xl font-bold ${config.color}`}>
              {(recommendation.confidence * 100).toFixed(0)}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-slate-400 text-sm mb-1">Most Influential</p>
            <p className="text-lg text-slate-300">{recommendation.mostInfluentialAgent.replace('Agent', '')}</p>
          </div>
        </div>
      </div>

      {/* Reasoning */}
      <div className="mb-6">
        <h3 className="text-cyan-400 font-semibold mb-3">Reasoning</h3>
        <p className="text-slate-300 leading-relaxed bg-slate-900/50 p-4 rounded-lg">
          {recommendation.reasoning}
        </p>
      </div>

      {/* Accepted Arguments */}
      <div className="mb-6">
        <h3 className="text-green-400 font-semibold mb-3 flex items-center gap-2">
          <CheckCircle className="w-5 h-5" />
          Accepted Arguments
        </h3>
        <div className="space-y-2">
          {recommendation.acceptedArguments.map((arg, index) => (
            <div key={index} className="flex items-start gap-2 bg-green-900/10 border border-green-500/20 rounded-lg p-3">
              <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
              <p className="text-slate-300 text-sm">{arg}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Rejected Arguments */}
      <div className="mb-6">
        <h3 className="text-red-400 font-semibold mb-3 flex items-center gap-2">
          <XCircle className="w-5 h-5" />
          Rejected Arguments
        </h3>
        <div className="space-y-2">
          {recommendation.rejectedArguments.map((arg, index) => (
            <div key={index} className="flex items-start gap-2 bg-red-900/10 border border-red-500/20 rounded-lg p-3">
              <XCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
              <p className="text-slate-300 text-sm">{arg}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Conditions (if applicable) */}
      {recommendation.conditions && recommendation.conditions.length > 0 && (
        <div className="mb-6">
          <h3 className="text-yellow-400 font-semibold mb-3 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            Required Conditions
          </h3>
          <div className="space-y-2">
            {recommendation.conditions.map((condition, index) => (
              <div key={index} className="flex items-start gap-2 bg-yellow-900/10 border border-yellow-500/20 rounded-lg p-3">
                <div className="w-6 h-6 rounded-full bg-yellow-500/20 flex items-center justify-center flex-shrink-0 text-yellow-400 text-xs font-bold">
                  {index + 1}
                </div>
                <p className="text-slate-300 text-sm">{condition}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Agent Influence */}
      <div>
        <h3 className="text-cyan-400 font-semibold mb-3 flex items-center gap-2">
          <TrendingUp className="w-5 h-5" />
          Agent Influence
        </h3>
        <div className="space-y-2">
          {Object.entries(recommendation.agentInfluence).map(([agent, influence]) => (
            <div key={agent} className="flex items-center gap-3">
              <span className="text-slate-400 text-sm w-32">{agent.replace('Agent', '')}</span>
              <div className="flex-1 h-6 bg-slate-900/50 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-500"
                  style={{ width: `${influence * 100}%` }}
                />
              </div>
              <span className="text-cyan-400 text-sm font-semibold w-12 text-right">
                {(influence * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Timestamp */}
      <div className="mt-6 pt-6 border-t border-slate-700 text-center">
        <p className="text-slate-500 text-sm">
          Decision Generated: {timestamp.toLocaleString()}
        </p>
      </div>
    </div>
  );
}

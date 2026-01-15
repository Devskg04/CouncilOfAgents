import React from 'react';
import { Decision } from '../types/aether';
import { Gavel, Scale, CheckCircle, XCircle, AlertCircle, RotateCcw, FileText } from 'lucide-react';

interface BailiffVerdictProps {
  decision: Decision;
  onReset: () => void;
  onReviewDebate: () => void;
}

export function BailiffVerdict({ decision, onReset, onReviewDebate }: BailiffVerdictProps) {
  const decisionConfig = {
    PROCEED: { 
      color: 'text-green-900', 
      bg: 'bg-green-100', 
      border: 'border-green-800',
      gradientFrom: 'from-green-800',
      gradientTo: 'to-green-900',
      label: 'APPROVED - PROCEED' 
    },
    REJECT: { 
      color: 'text-red-900', 
      bg: 'bg-red-100', 
      border: 'border-red-800',
      gradientFrom: 'from-red-800',
      gradientTo: 'to-red-900',
      label: 'REJECTED' 
    },
    CONDITIONAL_PROCEED: { 
      color: 'text-yellow-900', 
      bg: 'bg-yellow-100', 
      border: 'border-yellow-800',
      gradientFrom: 'from-yellow-800',
      gradientTo: 'to-yellow-900',
      label: 'CONDITIONAL APPROVAL' 
    },
    NEEDS_MORE_DATA: { 
      color: 'text-blue-900', 
      bg: 'bg-blue-100', 
      border: 'border-blue-800',
      gradientFrom: 'from-blue-800',
      gradientTo: 'to-blue-900',
      label: 'ADDITIONAL EVIDENCE REQUIRED' 
    },
  };

  const config = decisionConfig[decision.finalRecommendation.decision];

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-in fade-in duration-700">
      {/* Court is adjourned banner */}
      <div className={`bg-gradient-to-r ${config.gradientFrom} ${config.gradientTo} text-white p-6 rounded-lg shadow-2xl border-4 ${config.border}`}>
        <div className="flex items-center justify-center gap-4 mb-3">
          <Gavel className="w-12 h-12" />
          <h1 className="text-4xl font-serif">THE COURT HAS DECIDED</h1>
          <Gavel className="w-12 h-12" />
        </div>
        <p className="text-center text-lg opacity-90">Final Deliberation by the Bailiff</p>
      </div>

      {/* Problem Statement Recap */}
      <div className="bg-amber-50 border-4 border-amber-800 rounded-lg p-6 shadow-lg">
        <div className="flex items-center gap-2 mb-3">
          <FileText className="w-6 h-6 text-amber-900" />
          <h3 className="text-xl font-serif text-amber-900">Case Summary</h3>
        </div>
        <p className="text-amber-800 text-lg">{decision.problemStatement}</p>
        <div className="mt-4 flex gap-6 text-sm">
          <div>
            <span className="text-amber-700">Factors Analyzed:</span>
            <span className="text-amber-900 font-bold ml-2">{decision.factors.length}</span>
          </div>
          <div>
            <span className="text-amber-700">Overall Risk:</span>
            <span className={`font-bold ml-2 ${
              decision.overallRiskScore > 0.6 ? 'text-red-600' : 
              decision.overallRiskScore > 0.4 ? 'text-yellow-600' : 'text-green-600'
            }`}>
              {(decision.overallRiskScore * 100).toFixed(0)}%
            </span>
          </div>
          <div>
            <span className="text-amber-700">Disagreement:</span>
            <span className={`font-bold ml-2 ${
              decision.overallDisagreementScore > 0.6 ? 'text-red-600' : 
              decision.overallDisagreementScore > 0.4 ? 'text-yellow-600' : 'text-green-600'
            }`}>
              {(decision.overallDisagreementScore * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      {/* Final Verdict */}
      <div className={`${config.bg} border-8 ${config.border} rounded-lg p-10 shadow-2xl`}>
        <div className="text-center mb-8">
          <div className="inline-block bg-white border-4 border-current rounded-full p-6 mb-4">
            <Scale className={`w-20 h-20 ${config.color}`} />
          </div>
          <h2 className={`text-5xl font-serif ${config.color} mb-3`}>
            {config.label}
          </h2>
          <div className="flex items-center justify-center gap-8 mt-6">
            <div>
              <div className="text-sm text-gray-600 mb-1">Confidence Level</div>
              <div className={`text-4xl font-bold ${config.color}`}>
                {(decision.finalRecommendation.confidence * 100).toFixed(0)}%
              </div>
            </div>
            <div className="h-16 w-px bg-gray-400"></div>
            <div>
              <div className="text-sm text-gray-600 mb-1">Lead Agent</div>
              <div className={`text-2xl font-semibold ${config.color}`}>
                {decision.finalRecommendation.mostInfluentialAgent.replace('Agent', '')}
              </div>
            </div>
          </div>
        </div>

        {/* Reasoning */}
        <div className="bg-white border-2 border-gray-300 rounded-lg p-6 mb-6">
          <h3 className="text-xl font-serif text-gray-900 mb-3">Bailiff's Reasoning</h3>
          <p className="text-gray-800 text-lg leading-relaxed">
            {decision.finalRecommendation.reasoning}
          </p>
        </div>

        {/* Accepted Arguments */}
        <div className="bg-green-50 border-2 border-green-600 rounded-lg p-6 mb-6">
          <h3 className="text-xl font-serif text-green-900 mb-4 flex items-center gap-2">
            <CheckCircle className="w-6 h-6" />
            Arguments Upheld by the Court
          </h3>
          <div className="space-y-3">
            {decision.finalRecommendation.acceptedArguments.map((arg, index) => (
              <div key={index} className="flex items-start gap-3 bg-white border border-green-500 rounded-lg p-4">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <p className="text-gray-800">{arg}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Rejected Arguments */}
        <div className="bg-red-50 border-2 border-red-600 rounded-lg p-6 mb-6">
          <h3 className="text-xl font-serif text-red-900 mb-4 flex items-center gap-2">
            <XCircle className="w-6 h-6" />
            Arguments Dismissed by the Court
          </h3>
          <div className="space-y-3">
            {decision.finalRecommendation.rejectedArguments.map((arg, index) => (
              <div key={index} className="flex items-start gap-3 bg-white border border-red-500 rounded-lg p-4">
                <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-gray-800">{arg}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Conditions */}
        {decision.finalRecommendation.conditions && decision.finalRecommendation.conditions.length > 0 && (
          <div className="bg-yellow-50 border-2 border-yellow-600 rounded-lg p-6 mb-6">
            <h3 className="text-xl font-serif text-yellow-900 mb-4 flex items-center gap-2">
              <AlertCircle className="w-6 h-6" />
              Court-Mandated Conditions
            </h3>
            <div className="space-y-3">
              {decision.finalRecommendation.conditions.map((condition, index) => (
                <div key={index} className="flex items-start gap-3 bg-white border border-yellow-500 rounded-lg p-4">
                  <div className="w-7 h-7 bg-yellow-600 text-white rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0">
                    {index + 1}
                  </div>
                  <p className="text-gray-800">{condition}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Agent Influence Chart */}
        <div className="bg-gray-50 border-2 border-gray-400 rounded-lg p-6">
          <h3 className="text-xl font-serif text-gray-900 mb-4">Agent Influence on Final Decision</h3>
          <div className="space-y-3">
            {Object.entries(decision.finalRecommendation.agentInfluence).map(([agent, influence]) => (
              <div key={agent}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-gray-700 font-semibold">{agent.replace('Agent', ' Counsel')}</span>
                  <span className="text-gray-900 font-bold">{(influence * 100).toFixed(0)}%</span>
                </div>
                <div className="h-8 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${
                      agent === 'SupportingAgent' 
                        ? 'bg-gradient-to-r from-green-600 to-green-700' 
                        : 'bg-gradient-to-r from-red-600 to-red-700'
                    } transition-all duration-1000`}
                    style={{ width: `${influence * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-center gap-4 pt-6">
        <button
          onClick={onReviewDebate}
          className="flex items-center gap-2 px-6 py-3 bg-blue-700 hover:bg-blue-800 text-white rounded-lg transition-colors shadow-lg"
        >
          <FileText className="w-5 h-5" />
          Review Debate Transcript
        </button>
        <button
          onClick={onReset}
          className="flex items-center gap-2 px-6 py-3 bg-amber-800 hover:bg-amber-900 text-white rounded-lg transition-colors shadow-lg"
        >
          <RotateCcw className="w-5 h-5" />
          Start New Case
        </button>
      </div>

      {/* Timestamp */}
      <div className="text-center">
        <p className="text-gray-600 text-sm">
          Verdict issued on {decision.timestamp.toLocaleString()}
        </p>
      </div>
    </div>
  );
}

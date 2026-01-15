import React, { useState } from 'react';
import { Brain, History } from 'lucide-react';
import { Decision } from '../types/aether';
import { ProblemInput } from './ProblemInput';
import { FactorAnalysis } from './FactorAnalysis';
import { FinalDecisionPanel } from './FinalDecisionPanel';
import { MetricsPanel } from './MetricsPanel';
import { DecisionHistory } from './DecisionHistory';
import exampleImage from 'figma:asset/22853464ef664e2c412b0f54c5844c7af4513725.png';

interface AetherCommandCenterProps {
  currentDecision: Decision | null;
  decisionHistory: Decision[];
  isProcessing: boolean;
  onStartAnalysis: (problemStatement: string) => void;
  onClearDecision: () => void;
}

export function AetherCommandCenter({
  currentDecision,
  decisionHistory,
  isProcessing,
  onStartAnalysis,
  onClearDecision,
}: AetherCommandCenterProps) {
  const [showHistory, setShowHistory] = useState(false);

  return (
    <div className="min-h-screen p-4 md:p-8">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gradient-to-br from-cyan-400 to-blue-500 rounded-lg flex items-center justify-center shadow-lg shadow-cyan-500/50">
              <Brain className="w-10 h-10 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400">
                AETHER
              </h1>
              <p className="text-cyan-300 text-sm">Deliberative Decision Intelligence Platform</p>
            </div>
          </div>
          
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-cyan-500/30 rounded-lg text-cyan-300 transition-colors"
          >
            <History className="w-5 h-5" />
            <span>History ({decisionHistory.length})</span>
          </button>
        </div>

        {/* Project Info Bar */}
        <div className="bg-slate-800/50 border border-cyan-500/20 rounded-lg p-4 backdrop-blur-sm">
          <p className="text-slate-300 text-sm leading-relaxed">
            <span className="text-cyan-400 font-semibold">Multi-Agent Analysis:</span> Factor Extraction → 
            Supporting Arguments → Critical Analysis → Synthesis → Final Decision with Explainability
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto">
        {showHistory ? (
          <DecisionHistory 
            decisions={decisionHistory}
            onClose={() => setShowHistory(false)}
          />
        ) : (
          <>
            {/* Problem Input */}
            {!currentDecision && !isProcessing && (
              <ProblemInput onSubmit={onStartAnalysis} />
            )}

            {/* Processing State */}
            {isProcessing && (
              <div className="bg-slate-800/50 border border-cyan-500/30 rounded-lg p-12 text-center backdrop-blur-sm">
                <div className="w-20 h-20 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-6"></div>
                <h3 className="text-2xl text-cyan-300 mb-2">Aether is deliberating...</h3>
                <p className="text-slate-400">
                  Factor extraction → Agent debates → Synthesis → Final recommendation
                </p>
              </div>
            )}

            {/* Decision Analysis */}
            {currentDecision && (
              <div className="space-y-6">
                {/* Problem Statement Display */}
                <div className="bg-gradient-to-r from-slate-800/80 to-slate-800/50 border border-cyan-500/30 rounded-lg p-6 backdrop-blur-sm">
                  <h3 className="text-cyan-400 font-semibold mb-2">PROBLEM STATEMENT</h3>
                  <p className="text-slate-200 text-lg leading-relaxed">
                    {currentDecision.problemStatement}
                  </p>
                  <button
                    onClick={onClearDecision}
                    className="mt-4 text-sm text-slate-400 hover:text-cyan-400 transition-colors"
                  >
                    ← Start new analysis
                  </button>
                </div>

                {/* Metrics Overview */}
                <MetricsPanel
                  confidence={currentDecision.finalRecommendation.confidence}
                  riskScore={currentDecision.overallRiskScore}
                  disagreementScore={currentDecision.overallDisagreementScore}
                  agentInfluence={currentDecision.finalRecommendation.agentInfluence}
                />

                {/* Factor Analysis */}
                <FactorAnalysis factors={currentDecision.factors} />

                {/* Final Decision */}
                <FinalDecisionPanel
                  recommendation={currentDecision.finalRecommendation}
                  timestamp={currentDecision.timestamp}
                />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

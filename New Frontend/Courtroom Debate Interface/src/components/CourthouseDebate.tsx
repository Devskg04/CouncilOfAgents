import React, { useState, useEffect, useRef } from 'react';
import { Scale, Gavel } from 'lucide-react';
import { Decision, ProgressUpdate } from '../types/aether';
import { ProblemInput } from './ProblemInput';
import { LiveDebateArena } from './LiveDebateArena';
import { BailiffVerdict } from './BailiffVerdict';

interface CourthouseDebateProps {
  currentDecision: Decision | null;
  isProcessing: boolean;
  onStartAnalysis: (problemStatement: string) => void;
  onClearDecision: () => void;
  progressUpdates?: ProgressUpdate[];
}

export function CourthouseDebate({
  currentDecision,
  isProcessing,
  onStartAnalysis,
  onClearDecision,
  progressUpdates = [],
}: CourthouseDebateProps) {
  const [currentFactorIndex, setCurrentFactorIndex] = useState(0);
  const [showVerdict, setShowVerdict] = useState(false);

  useEffect(() => {
    if (currentDecision) {
      setCurrentFactorIndex(0);
      setShowVerdict(false);
    }
  }, [currentDecision]);

  const handleNextFactor = () => {
    if (currentDecision && currentFactorIndex < currentDecision.factors.length - 1) {
      setCurrentFactorIndex(prev => prev + 1);
    } else {
      setShowVerdict(true);
    }
  };

  const handlePreviousFactor = () => {
    if (currentFactorIndex > 0) {
      setCurrentFactorIndex(prev => prev - 1);
    }
  };

  return (
    <div className="min-h-screen">
      {/* Courthouse Header */}
      <div className="bg-gradient-to-r from-amber-900 via-amber-800 to-amber-900 border-b-4 border-amber-950 shadow-2xl">
        <div className="max-w-7xl mx-auto py-6 px-4">
          <div className="flex items-center justify-center gap-4">
            <Scale className="w-12 h-12 text-amber-200" />
            <div className="text-center">
              <h1 className="text-4xl font-serif text-amber-50">AETHER COURTHOUSE</h1>
              <p className="text-amber-200 text-sm mt-1">Deliberative Decision Intelligence System</p>
            </div>
            <Gavel className="w-12 h-12 text-amber-200" />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-4 md:p-8">
        {!currentDecision && !isProcessing && (
          <ProblemInput onSubmit={onStartAnalysis} />
        )}

        {isProcessing && (
          <div className="bg-amber-50 border-4 border-amber-800 rounded-lg p-8 shadow-xl">
            <div className="flex flex-col items-center">
              <div className="w-20 h-20 border-4 border-amber-800 border-t-transparent rounded-full animate-spin mb-6"></div>
              <h3 className="text-2xl text-amber-900 mb-4 font-serif">Court in Session...</h3>
              <p className="text-amber-700">Agents are deliberating...</p>
            </div>
          </div>
        )}

        {currentDecision && !showVerdict && (
          <LiveDebateArena
            decision={currentDecision}
            currentFactorIndex={currentFactorIndex}
            onNextFactor={handleNextFactor}
            onPreviousFactor={handlePreviousFactor}
            onReset={onClearDecision}
          />
        )}

        {currentDecision && showVerdict && (
          <BailiffVerdict
            decision={currentDecision}
            onReset={onClearDecision}
            onReviewDebate={() => setShowVerdict(false)}
          />
        )}
      </div>
    </div>
  );
}

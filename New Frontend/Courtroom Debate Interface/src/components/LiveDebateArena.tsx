import React, { useState, useEffect, useRef } from 'react';
import { Decision, AgentMessage } from '../types/aether';
import { UserCheck, UserX, ChevronLeft, ChevronRight, Flag, ArrowRight, Scale } from 'lucide-react';

interface LiveDebateArenaProps {
  decision: Decision;
  currentFactorIndex: number;
  onNextFactor: () => void;
  onPreviousFactor: () => void;
  onReset: () => void;
}

export function LiveDebateArena({
  decision,
  currentFactorIndex,
  onNextFactor,
  onPreviousFactor,
  onReset,
}: LiveDebateArenaProps) {
  const currentFactor = decision.factors[currentFactorIndex];
  const [visibleMessages, setVisibleMessages] = useState<AgentMessage[]>([]);
  const [isAnimating, setIsAnimating] = useState(false);
  const debateEndRef = useRef<HTMLDivElement>(null);

  // Animate messages appearing one by one
  useEffect(() => {
    setVisibleMessages([]);
    setIsAnimating(true);

    let index = 0;
    const interval = setInterval(() => {
      if (index < currentFactor.debate.length) {
        const message = currentFactor.debate[index];
        if (message) {
          setVisibleMessages(prev => [...prev, message]);
        }
        index++;
      } else {
        setIsAnimating(false);
        clearInterval(interval);
      }
    }, 800);

    return () => clearInterval(interval);
  }, [currentFactorIndex, decision]);

  // Auto scroll to latest message
  useEffect(() => {
    debateEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [visibleMessages]);

  const isLastFactor = currentFactorIndex === decision.factors.length - 1;
  const isFirstFactor = currentFactorIndex === 0;

  return (
    <div className="space-y-6">
      {/* Problem Statement Banner */}
      <div className="bg-amber-100 border-4 border-amber-800 rounded-lg p-6 shadow-lg">
        <div className="flex items-center gap-3 mb-2">
          <Flag className="w-6 h-6 text-amber-900" />
          <h3 className="text-amber-900 font-serif text-lg">CASE UNDER DELIBERATION</h3>
        </div>
        <p className="text-amber-800 text-xl leading-relaxed">{decision.problemStatement}</p>
        <button
          onClick={onReset}
          className="mt-3 text-sm text-amber-700 hover:text-amber-900 underline"
        >
          ← Start new case
        </button>
      </div>

      {/* Current Factor Banner */}
      <div className="bg-gradient-to-r from-amber-800 to-amber-900 text-white p-4 rounded-lg shadow-lg border-2 border-amber-950">
        <div className="text-center">
          <div className="text-sm text-amber-200 mb-1">
            Factor {currentFactorIndex + 1} of {decision.factors.length}
          </div>
          <h2 className="text-3xl font-serif mb-1">{currentFactor.name}</h2>
          <p className="text-amber-200 text-sm">{currentFactor.description}</p>
        </div>
      </div>

      {/* Courtroom Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto_1fr] gap-6">
        {/* Left Agent - Supporting Counsel */}
        <div className="bg-green-50 border-4 border-green-800 rounded-lg p-6 shadow-xl">
          <div className="flex items-center gap-3 mb-6 pb-4 border-b-2 border-green-800">
            <div className="w-12 h-12 bg-green-800 rounded-full flex items-center justify-center">
              <UserCheck className="w-7 h-7 text-green-50" />
            </div>
            <div>
              <h3 className="text-2xl font-serif text-green-900">Supporting Counsel</h3>
              <p className="text-green-700 text-sm">Presenting affirmative arguments</p>
            </div>
          </div>

          {/* Left Agent Arguments */}
          <div className="space-y-3">
            {visibleMessages
              .filter(msg => msg.agent === 'SupportingAgent')
              .map((msg, index) => (
                <div
                  key={msg.id}
                  className="bg-white border-2 border-green-700 rounded-lg p-4 shadow-md animate-in fade-in slide-in-from-left-8 duration-500"
                >
                  <div className="flex items-start gap-2 mb-2">
                    <div className="bg-green-700 text-white text-xs px-2 py-1 rounded-full font-semibold">
                      Round {msg.round}
                    </div>
                    <span className="text-xs text-gray-500 ml-auto">
                      {msg.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-gray-800 leading-relaxed">{msg.content}</p>
                </div>
              ))}
          </div>
        </div>

        {/* Center Divider */}
        <div className="hidden lg:flex flex-col items-center justify-center px-4">
          <div className="h-full w-1 bg-gradient-to-b from-amber-300 via-amber-600 to-amber-300 rounded-full"></div>
          <div className="absolute">
            <Scale className="w-16 h-16 text-amber-800" />
          </div>
        </div>

        {/* Right Agent - Opposition Counsel */}
        <div className="bg-red-50 border-4 border-red-800 rounded-lg p-6 shadow-xl">
          <div className="flex items-center gap-3 mb-6 pb-4 border-b-2 border-red-800">
            <div className="w-12 h-12 bg-red-800 rounded-full flex items-center justify-center">
              <UserX className="w-7 h-7 text-red-50" />
            </div>
            <div>
              <h3 className="text-2xl font-serif text-red-900">Opposition Counsel</h3>
              <p className="text-red-700 text-sm">Presenting counter-arguments</p>
            </div>
          </div>

          {/* Right Agent Arguments */}
          <div className="space-y-3">
            {visibleMessages
              .filter(msg => msg.agent === 'CriticAgent')
              .map((msg, index) => (
                <div
                  key={msg.id}
                  className="bg-white border-2 border-red-700 rounded-lg p-4 shadow-md animate-in fade-in slide-in-from-right-8 duration-500"
                >
                  <div className="flex items-start gap-2 mb-2">
                    <div className="bg-red-700 text-white text-xs px-2 py-1 rounded-full font-semibold">
                      Round {msg.round}
                    </div>
                    <span className="text-xs text-gray-500 ml-auto">
                      {msg.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-gray-800 leading-relaxed">{msg.content}</p>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Scroll anchor */}
      <div ref={debateEndRef} />

      {/* Factor Synthesis */}
      {!isAnimating && (
        <div className="bg-purple-50 border-4 border-purple-800 rounded-lg p-6 shadow-xl animate-in fade-in duration-700">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-purple-800 rounded-full flex items-center justify-center text-white font-bold">
              S
            </div>
            <h3 className="text-2xl font-serif text-purple-900">Court Clerk Summary</h3>
          </div>
          <p className="text-purple-900 mb-4 leading-relaxed">{currentFactor.synthesis.summary}</p>
          <div className="space-y-2">
            <p className="text-purple-800 font-semibold text-sm">Key Points:</p>
            {currentFactor.synthesis.keyPoints.map((point, index) => (
              <div key={index} className="flex items-start gap-2">
                <div className="w-5 h-5 bg-purple-800 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0 mt-0.5">
                  {index + 1}
                </div>
                <p className="text-purple-800 text-sm">{point}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Navigation Controls */}
      {!isAnimating && (
        <div className="flex items-center justify-between gap-4 pt-4">
          <button
            onClick={onPreviousFactor}
            disabled={isFirstFactor}
            className="flex items-center gap-2 px-6 py-3 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-lg transition-colors shadow-lg"
          >
            <ChevronLeft className="w-5 h-5" />
            Previous Factor
          </button>

          <div className="text-center">
            <div className="text-sm text-gray-600">Disagreement Score</div>
            <div className={`text-2xl font-bold ${currentFactor.disagreementScore > 0.6 ? 'text-red-600' :
              currentFactor.disagreementScore > 0.4 ? 'text-yellow-600' : 'text-green-600'
              }`}>
              {(currentFactor.disagreementScore * 100).toFixed(0)}%
            </div>
          </div>

          <button
            onClick={onNextFactor}
            className="flex items-center gap-2 px-6 py-3 bg-amber-800 hover:bg-amber-900 text-white rounded-lg transition-colors shadow-lg"
          >
            {isLastFactor ? (
              <>
                Proceed to Verdict
                <ArrowRight className="w-5 h-5" />
              </>
            ) : (
              <>
                Next Factor
                <ChevronRight className="w-5 h-5" />
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
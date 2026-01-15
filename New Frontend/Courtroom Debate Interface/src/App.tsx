import React, { useState } from 'react';
import { CourthouseDebate } from './components/CourthouseDebate';
import { Decision, ProgressUpdate } from './types/aether';
import { apiClient } from './services/api';
import { transformBackendResponse } from './utils/dataTransformer';

function App() {
  const [currentDecision, setCurrentDecision] = useState<Decision | null>(null);
  const [decisionHistory, setDecisionHistory] = useState<Decision[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progressUpdates, setProgressUpdates] = useState<ProgressUpdate[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Function to start analysis with backend API
  const startAnalysis = async (problemStatement: string) => {
    setIsProcessing(true);
    setError(null);
    setProgressUpdates([]);
    setCurrentDecision(null);

    try {
      // Use SSE for real-time updates
      const cleanup = await apiClient.analyzeStream(
        problemStatement,
        // Progress callback
        (update: ProgressUpdate) => {
          setProgressUpdates(prev => [...prev, update]);
        },
        // Complete callback
        (response) => {
          try {
            const decision = transformBackendResponse(response, problemStatement);
            setCurrentDecision(decision);
            setDecisionHistory(prev => [decision, ...prev]);
            setIsProcessing(false);
          } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to process analysis results';
            setError(errorMessage);
            setIsProcessing(false);
          }
        },
        // Error callback
        (err) => {
          setError(err.message);
          setIsProcessing(false);
        }
      );

      // Store cleanup function if needed
      // You could add this to component state if you want to allow cancellation
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start analysis';
      setError(errorMessage);
      setIsProcessing(false);
    }
  };

  const clearCurrentDecision = () => {
    setCurrentDecision(null);
    setProgressUpdates([]);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-stone-100 to-neutral-100">
      {error && (
        <div className="fixed top-4 right-4 bg-red-100 border-2 border-red-600 text-red-800 px-6 py-4 rounded-lg shadow-lg z-50 max-w-md">
          <div className="flex items-start gap-3">
            <svg className="w-6 h-6 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div>
              <h3 className="font-bold mb-1">Error</h3>
              <p className="text-sm">{error}</p>
              <button
                onClick={() => setError(null)}
                className="mt-2 text-sm underline hover:no-underline"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      <CourthouseDebate
        currentDecision={currentDecision}
        isProcessing={isProcessing}
        onStartAnalysis={startAnalysis}
        onClearDecision={clearCurrentDecision}
        progressUpdates={progressUpdates}
      />
    </div>
  );
}

export default App;
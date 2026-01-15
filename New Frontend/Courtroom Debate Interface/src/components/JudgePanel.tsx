import React, { useState } from 'react';
import { Scale, Gavel, RotateCcw, FileText } from 'lucide-react';
import { JudgeReport } from '../App';

interface JudgePanelProps {
  judgeReport: JudgeReport | null;
  isDebating: boolean;
  onSetFinalReport?: (summary: string, verdict: string) => void;
  onReset?: () => void;
  totalArguments: number;
}

export function JudgePanel({
  judgeReport,
  isDebating,
  onSetFinalReport,
  onReset,
  totalArguments,
}: JudgePanelProps) {
  const [showReportForm, setShowReportForm] = useState(false);
  const [summary, setSummary] = useState('');
  const [verdict, setVerdict] = useState('');

  const handleSubmitReport = (e: React.FormEvent) => {
    e.preventDefault();
    if (summary.trim() && verdict.trim() && onSetFinalReport) {
      onSetFinalReport(summary, verdict);
      setSummary('');
      setVerdict('');
      setShowReportForm(false);
    }
  };

  return (
    <div className="bg-gradient-to-br from-amber-50 to-amber-100 rounded-lg shadow-2xl border-4 border-amber-700 overflow-hidden">
      {/* Judge Header */}
      <div className="bg-gradient-to-r from-amber-800 to-amber-900 text-white p-6">
        <div className="flex items-center justify-center gap-4">
          <Scale className="w-10 h-10" />
          <div className="text-center">
            <h2 className="text-3xl font-serif">The Judge</h2>
            <p className="text-sm opacity-90 mt-1">Presiding Officer</p>
          </div>
          <Gavel className="w-10 h-10" />
        </div>
      </div>

      {/* Judge Content */}
      <div className="p-6">
        {!judgeReport && isDebating ? (
          <div className="text-center py-8">
            <div className="mb-6">
              <div className="w-24 h-24 bg-amber-200 rounded-full mx-auto flex items-center justify-center mb-4">
                <FileText className="w-12 h-12 text-amber-800" />
              </div>
              <p className="text-gray-700 mb-2">
                Debate in progress...
              </p>
              <p className="text-sm text-gray-600">
                {totalArguments} total arguments presented
              </p>
            </div>

            {onSetFinalReport && !showReportForm && (
              <button
                onClick={() => setShowReportForm(true)}
                className="bg-amber-700 hover:bg-amber-800 text-white px-6 py-3 rounded-lg transition-colors font-semibold inline-flex items-center gap-2"
              >
                <Gavel className="w-5 h-5" />
                Issue Final Report
              </button>
            )}

            {showReportForm && (
              <form onSubmit={handleSubmitReport} className="mt-6 max-w-2xl mx-auto">
                <div className="space-y-4 text-left">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Summary
                    </label>
                    <textarea
                      value={summary}
                      onChange={(e) => setSummary(e.target.value)}
                      placeholder="Enter the summary of arguments..."
                      rows={4}
                      className="w-full px-4 py-3 border-2 border-amber-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Verdict
                    </label>
                    <textarea
                      value={verdict}
                      onChange={(e) => setVerdict(e.target.value)}
                      placeholder="Enter the final verdict..."
                      rows={3}
                      className="w-full px-4 py-3 border-2 border-amber-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                      required
                    />
                  </div>
                  <div className="flex gap-3 justify-center">
                    <button
                      type="button"
                      onClick={() => setShowReportForm(false)}
                      className="px-6 py-2 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-6 py-2 bg-amber-700 hover:bg-amber-800 text-white rounded-lg transition-colors font-semibold"
                    >
                      Submit Report
                    </button>
                  </div>
                </div>
              </form>
            )}
          </div>
        ) : judgeReport ? (
          <div className="space-y-6">
            {/* Final Report */}
            <div className="bg-white rounded-lg p-6 shadow-lg border-2 border-amber-300">
              <div className="flex items-center gap-3 mb-4 pb-4 border-b-2 border-amber-200">
                <Gavel className="w-6 h-6 text-amber-700" />
                <h3 className="text-2xl font-serif text-amber-900">Final Report</h3>
              </div>
              
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold text-gray-700 mb-2">Summary</h4>
                  <p className="text-gray-800 leading-relaxed">{judgeReport.summary}</p>
                </div>
                
                <div className="pt-4 border-t-2 border-amber-100">
                  <h4 className="font-semibold text-gray-700 mb-2">Verdict</h4>
                  <p className="text-gray-900 font-medium leading-relaxed">{judgeReport.verdict}</p>
                </div>
              </div>
            </div>

            {/* Reset Button */}
            {onReset && (
              <div className="text-center">
                <button
                  onClick={onReset}
                  className="bg-gray-700 hover:bg-gray-800 text-white px-6 py-3 rounded-lg transition-colors font-semibold inline-flex items-center gap-2"
                >
                  <RotateCcw className="w-5 h-5" />
                  Start New Debate
                </button>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}

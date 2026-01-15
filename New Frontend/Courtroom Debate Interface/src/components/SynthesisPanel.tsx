import React from 'react';
import { Synthesis } from '../types/aether';
import { GitMerge, CheckCircle2 } from 'lucide-react';

interface SynthesisPanelProps {
  synthesis: Synthesis;
}

export function SynthesisPanel({ synthesis }: SynthesisPanelProps) {
  return (
    <div className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-5">
      <div className="flex items-center gap-2 mb-4">
        <GitMerge className="w-5 h-5 text-purple-400" />
        <h4 className="text-lg text-purple-400 font-semibold">Synthesis</h4>
        <span className="text-xs text-purple-400/60 ml-auto">{synthesis.synthesizedBy}</span>
      </div>

      <p className="text-slate-300 leading-relaxed mb-4">{synthesis.summary}</p>

      <div className="space-y-2">
        <p className="text-sm text-purple-400 font-semibold">Key Points:</p>
        {synthesis.keyPoints.map((point, index) => (
          <div key={index} className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-purple-400 mt-0.5 flex-shrink-0" />
            <p className="text-slate-400 text-sm">{point}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

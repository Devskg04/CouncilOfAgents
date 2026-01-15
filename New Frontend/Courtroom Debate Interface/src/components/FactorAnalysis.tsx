import React, { useState } from 'react';
import { Factor } from '../types/aether';
import { FactorCard } from './FactorCard';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface FactorAnalysisProps {
  factors: Factor[];
}

export function FactorAnalysis({ factors }: FactorAnalysisProps) {
  const [expandedFactor, setExpandedFactor] = useState<string | null>(factors[0]?.id || null);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl text-cyan-300 font-semibold mb-4">Factor Analysis & Agent Debates</h2>
      
      {factors.map((factor) => (
        <FactorCard
          key={factor.id}
          factor={factor}
          isExpanded={expandedFactor === factor.id}
          onToggle={() => setExpandedFactor(expandedFactor === factor.id ? null : factor.id)}
        />
      ))}
    </div>
  );
}

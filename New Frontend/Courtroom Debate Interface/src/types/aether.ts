export interface AgentMessage {
  id: string;
  agent: 'SupportingAgent' | 'CriticAgent' | 'SynthesizerAgent' | 'FinalDecisionAgent';
  content: string;
  timestamp: Date;
  round?: number;
}

export interface Synthesis {
  summary: string;
  keyPoints: string[];
  synthesizedBy: string;
}

export interface Factor {
  id: string;
  name: string;
  description: string;
  debate: AgentMessage[];
  synthesis: Synthesis;
  disagreementScore: number;
  weight: number;
}

export interface FinalRecommendation {
  decision: 'PROCEED' | 'REJECT' | 'CONDITIONAL_PROCEED' | 'NEEDS_MORE_DATA';
  confidence: number;
  reasoning: string;
  acceptedArguments: string[];
  rejectedArguments: string[];
  conditions?: string[];
  mostInfluentialAgent: string;
  agentInfluence: Record<string, number>;
}

export interface Decision {
  id: string;
  problemStatement: string;
  timestamp: Date;
  factors: Factor[];
  finalRecommendation: FinalRecommendation;
  overallRiskScore: number;
  overallDisagreementScore: number;
  humanOverride?: {
    decision: string;
    reason: string;
    timestamp: Date;
  };
}

export interface ProgressUpdate {
  stage: string;
  message: string;
  data?: any;
}

import React from 'react';
import { Scale, Gavel } from 'lucide-react';
import { AgentPanel } from './AgentPanel';
import { JudgePanel } from './JudgePanel';
import { AgentArgument, JudgeReport } from '../App';

interface CourtRoomProps {
  leftAgentName: string;
  rightAgentName: string;
  leftArguments: AgentArgument[];
  rightArguments: AgentArgument[];
  judgeReport: JudgeReport | null;
  isDebating: boolean;
  onAddLeftArgument?: (text: string) => void;
  onAddRightArgument?: (text: string) => void;
  onSetFinalReport?: (summary: string, verdict: string) => void;
  onReset?: () => void;
}

export function CourtRoom({
  leftAgentName,
  rightAgentName,
  leftArguments,
  rightArguments,
  judgeReport,
  isDebating,
  onAddLeftArgument,
  onAddRightArgument,
  onSetFinalReport,
  onReset,
}: CourtRoomProps) {
  return (
    <div className="w-full min-h-screen p-4 md:p-8">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="flex items-center justify-center gap-3 mb-3">
          <Scale className="w-10 h-10 text-amber-700" />
          <h1 className="text-4xl font-serif text-amber-900">AI Courtroom Debate</h1>
          <Gavel className="w-10 h-10 text-amber-700" />
        </div>
        <div className="h-1 w-32 bg-amber-700 mx-auto rounded-full"></div>
      </div>

      {/* Main Courtroom Layout */}
      <div className="max-w-7xl mx-auto">
        {/* Debate Panels - Side by Side */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Left Agent */}
          <AgentPanel
            agentName={leftAgentName}
            arguments={leftArguments}
            position="left"
            onAddArgument={onAddLeftArgument}
            isDebating={isDebating}
          />

          {/* Right Agent */}
          <AgentPanel
            agentName={rightAgentName}
            arguments={rightArguments}
            position="right"
            onAddArgument={onAddRightArgument}
            isDebating={isDebating}
          />
        </div>

        {/* Judge Panel - Center Bottom */}
        <JudgePanel
          judgeReport={judgeReport}
          isDebating={isDebating}
          onSetFinalReport={onSetFinalReport}
          onReset={onReset}
          totalArguments={leftArguments.length + rightArguments.length}
        />
      </div>

      {/* Visual Courtroom Decoration */}
      <div className="fixed bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-amber-900/20 to-transparent pointer-events-none"></div>
    </div>
  );
}

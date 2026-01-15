import React from 'react';
import { AgentMessage } from '../types/aether';
import { UserCheck, UserX, ArrowRight } from 'lucide-react';

interface DebateThreadProps {
  messages: AgentMessage[];
}

export function DebateThread({ messages }: DebateThreadProps) {
  const rounds = messages.reduce((acc, msg) => {
    const round = msg.round || 1;
    if (!acc[round]) acc[round] = [];
    acc[round].push(msg);
    return acc;
  }, {} as Record<number, AgentMessage[]>);

  return (
    <div className="space-y-6">
      {Object.entries(rounds).map(([roundNum, roundMessages]) => (
        <div key={roundNum} className="space-y-3">
          <div className="flex items-center gap-2 mb-3">
            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent"></div>
            <span className="text-xs text-cyan-400 font-semibold px-3 py-1 bg-cyan-500/10 rounded-full border border-cyan-500/30">
              ROUND {roundNum}
            </span>
            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent"></div>
          </div>

          <div className="space-y-3">
            {roundMessages.map((message, index) => (
              <div key={message.id}>
                <AgentMessageCard message={message} />
                {index < roundMessages.length - 1 && (
                  <div className="flex justify-center my-2">
                    <ArrowRight className="w-5 h-5 text-slate-600" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function AgentMessageCard({ message }: { message: AgentMessage }) {
  const isSupporting = message.agent === 'SupportingAgent';
  
  const agentColors = {
    SupportingAgent: {
      bg: 'bg-green-900/20',
      border: 'border-green-500/30',
      text: 'text-green-400',
      icon: UserCheck,
    },
    CriticAgent: {
      bg: 'bg-red-900/20',
      border: 'border-red-500/30',
      text: 'text-red-400',
      icon: UserX,
    },
  };

  const colors = agentColors[message.agent as keyof typeof agentColors] || agentColors.SupportingAgent;
  const Icon = colors.icon;

  return (
    <div className={`${colors.bg} border ${colors.border} rounded-lg p-4`}>
      <div className="flex items-start gap-3">
        <div className={`${colors.bg} border ${colors.border} rounded-full p-2 flex-shrink-0`}>
          <Icon className={`w-5 h-5 ${colors.text}`} />
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <h5 className={`${colors.text} font-semibold text-sm`}>
              {message.agent.replace('Agent', ' Agent')}
            </h5>
            <span className="text-xs text-slate-500">
              {message.timestamp.toLocaleTimeString()}
            </span>
          </div>
          <p className="text-slate-300 leading-relaxed">{message.content}</p>
        </div>
      </div>
    </div>
  );
}

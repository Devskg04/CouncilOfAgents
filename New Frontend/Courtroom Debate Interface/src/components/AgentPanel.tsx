import React, { useState } from 'react';
import { User, Send } from 'lucide-react';
import { AgentArgument } from '../App';

interface AgentPanelProps {
  agentName: string;
  arguments: AgentArgument[];
  position: 'left' | 'right';
  onAddArgument?: (text: string) => void;
  isDebating: boolean;
}

export function AgentPanel({
  agentName,
  arguments: args,
  position,
  onAddArgument,
  isDebating,
}: AgentPanelProps) {
  const [inputValue, setInputValue] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && onAddArgument) {
      onAddArgument(inputValue.trim());
      setInputValue('');
    }
  };

  const bgColor = position === 'left' ? 'bg-blue-50' : 'bg-red-50';
  const accentColor = position === 'left' ? 'text-blue-700' : 'text-red-700';
  const borderColor = position === 'left' ? 'border-blue-200' : 'border-red-200';
  const buttonColor = position === 'left' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-red-600 hover:bg-red-700';

  return (
    <div className={`${bgColor} rounded-lg shadow-xl border-2 ${borderColor} overflow-hidden flex flex-col h-[600px]`}>
      {/* Agent Header */}
      <div className={`${position === 'left' ? 'bg-blue-700' : 'bg-red-700'} text-white p-4`}>
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
            <User className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-semibold">{agentName}</h2>
            <p className="text-sm opacity-90">
              {position === 'left' ? 'Prosecution' : 'Defense'} • {args.length} arguments
            </p>
          </div>
        </div>
      </div>

      {/* Arguments List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {args.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <p>No arguments presented yet.</p>
          </div>
        ) : (
          args.map((arg, index) => (
            <div
              key={arg.id}
              className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 animate-in fade-in slide-in-from-bottom-4 duration-300"
            >
              <div className="flex items-start gap-3">
                <div className={`${position === 'left' ? 'bg-blue-100 text-blue-700' : 'bg-red-100 text-red-700'} w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 font-semibold text-sm`}>
                  {index + 1}
                </div>
                <div className="flex-1">
                  <p className="text-gray-800">{arg.text}</p>
                  <p className="text-xs text-gray-500 mt-2">
                    {arg.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Input Form */}
      {isDebating && onAddArgument && (
        <div className="p-4 bg-white border-t-2 border-gray-200">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Enter argument..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-0 focus:ring-gray-400"
            />
            <button
              type="submit"
              disabled={!inputValue.trim()}
              className={`${buttonColor} text-white px-4 py-2 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2`}
            >
              <Send className="w-4 h-4" />
              <span className="hidden sm:inline">Send</span>
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

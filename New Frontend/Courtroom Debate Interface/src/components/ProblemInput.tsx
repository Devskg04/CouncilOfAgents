import React, { useState } from 'react';
import { Send, FileText, Upload, X } from 'lucide-react';

interface ProblemInputProps {
  onSubmit: (problemStatement: string) => void;
}

export function ProblemInput({ onSubmit }: ProblemInputProps) {
  const [input, setInput] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && (file.type === 'application/pdf' || file.type === 'text/plain')) {
      setSelectedFile(file);
      
      // If it's a text file, read and populate the textarea
      if (file.type === 'text/plain') {
        const reader = new FileReader();
        reader.onload = (event) => {
          const text = event.target?.result as string;
          setInput(text);
        };
        reader.readAsText(file);
      } else {
        // For PDF files, just show the file name
        setInput(`[PDF File: ${file.name}] - Content will be processed by backend`);
      }
    } else {
      alert('Please select a PDF or TXT file');
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setInput('');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      onSubmit(input.trim());
      setInput('');
      setSelectedFile(null);
    }
  };

  const exampleProblems = [
    'Should we launch a new AI-powered product in Q2?',
    'Evaluate acquisition of Company X for $50M',
    'Assess feasibility of entering the European market',
  ];

  return (
    <div className="bg-amber-50 border-4 border-amber-800 rounded-lg p-8 shadow-xl">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <FileText className="w-8 h-8 text-amber-900" />
          <h2 className="text-2xl font-serif text-amber-900">Submit Problem Statement</h2>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* File Upload Section */}
          <div className="bg-white border-2 border-amber-700 rounded-lg p-4">
            <label className="flex items-center justify-center gap-2 cursor-pointer">
              <input
                type="file"
                accept=".pdf,.txt"
                onChange={handleFileChange}
                className="hidden"
              />
              <Upload className="w-5 h-5 text-amber-800" />
              <span className="text-amber-900 font-semibold">
                Upload PDF or TXT file
              </span>
            </label>
            
            {selectedFile && (
              <div className="mt-3 flex items-center justify-between bg-amber-100 border border-amber-600 rounded-lg p-3">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-amber-800" />
                  <span className="text-sm text-amber-900">{selectedFile.name}</span>
                  <span className="text-xs text-amber-700">
                    ({(selectedFile.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
                <button
                  type="button"
                  onClick={handleRemoveFile}
                  className="text-red-600 hover:text-red-800 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>

          <div className="text-center text-sm text-amber-700">OR</div>

          {/* Text Input */}
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter your decision problem or question for multi-agent analysis..."
            rows={6}
            className="w-full px-4 py-3 bg-white border-2 border-amber-700 rounded-lg text-gray-800 placeholder-amber-600/50 focus:outline-none focus:ring-2 focus:ring-amber-600 focus:border-amber-600 resize-none"
          />

          <div className="flex items-center justify-between">
            <p className="text-sm text-amber-800">
              Aether will extract factors and conduct structured agent debates
            </p>
            <button
              type="submit"
              disabled={!input.trim()}
              className="flex items-center gap-2 px-6 py-3 bg-amber-800 hover:bg-amber-900 disabled:bg-amber-400 disabled:cursor-not-allowed text-white rounded-lg transition-all shadow-lg disabled:shadow-none"
            >
              <Send className="w-5 h-5" />
              Start Analysis
            </button>
          </div>
        </form>

        {/* Example Problems */}
        <div className="mt-8 pt-6 border-t-2 border-amber-700">
          <p className="text-sm text-amber-800 mb-3 font-semibold">Example problems:</p>
          <div className="flex flex-wrap gap-2">
            {exampleProblems.map((example, index) => (
              <button
                key={index}
                onClick={() => setInput(example)}
                className="px-3 py-2 bg-white hover:bg-amber-100 border-2 border-amber-700 hover:border-amber-800 rounded-lg text-sm text-amber-900 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
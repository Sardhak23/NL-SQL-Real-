import React, { useState, useRef, useEffect } from 'react';
import { ArrowUpRight, Loader2, CornerDownLeft, Sparkles, X } from 'lucide-react';
import { PromptPills } from './PromptPills';

interface QueryComposerProps {
  onSubmit: (question: string) => void;
  isExecuting: boolean;
  initialValue?: string;
}

export const QueryComposer: React.FC<QueryComposerProps> = ({
  onSubmit,
  isExecuting,
  initialValue = '',
}) => {
  const [question, setQuestion] = useState(initialValue);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (initialValue) {
      setQuestion(initialValue);
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
        textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
      }
    }
  }, [initialValue]);

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setQuestion(e.target.value);
    // Auto-resize textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    if (!question.trim() || isExecuting) return;
    onSubmit(question.trim());
  };

  const handleSelectPrompt = (prompt: string) => {
    setQuestion(prompt);
    onSubmit(prompt);
  };

  const handleClear = () => {
    setQuestion('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.focus();
    }
  };

  return (
    <div className="space-y-2.5">
      {/* Suggestions Carousel */}
      <PromptPills onSelectPrompt={handleSelectPrompt} disabled={isExecuting} />

      {/* Main Composer Box */}
      <div className="relative rounded-2xl border border-zinc-800/80 bg-zinc-900/90 p-2 shadow-2xl transition-all focus-within:border-indigo-500/80 focus-within:ring-2 focus-within:ring-indigo-500/20 backdrop-blur-xl">
        <div className="flex items-start space-x-2 px-2 pt-1">
          <Sparkles className="mt-1 h-4 w-4 text-indigo-400 shrink-0" />
          <textarea
            ref={textareaRef}
            value={question}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            disabled={isExecuting}
            rows={1}
            placeholder="Ask anything about 500,000+ orders, revenue, customer cohorts, margins, or inventory..."
            className="w-full resize-none bg-transparent py-1 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none disabled:opacity-50 scrollbar-none font-sans"
          />

          {question && (
            <button
              onClick={handleClear}
              disabled={isExecuting}
              title="Clear input"
              className="p-1 text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          )}

          {/* Submit Action Button */}
          <button
            onClick={handleSubmit}
            disabled={!question.trim() || isExecuting}
            className="flex h-8 items-center space-x-1.5 rounded-xl bg-gradient-to-r from-indigo-500 to-indigo-600 px-3.5 text-xs font-semibold text-white shadow-md shadow-indigo-500/25 transition-all hover:from-indigo-400 hover:to-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
          >
            {isExecuting ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                <span>Running</span>
              </>
            ) : (
              <>
                <span>Run</span>
                <CornerDownLeft className="h-3 w-3 opacity-80" />
              </>
            )}
          </button>
        </div>

        {/* Footer Hint Bar */}
        <div className="mt-2 flex items-center justify-between border-t border-zinc-800/50 px-2 pt-1.5 text-[11px] text-zinc-500">
          <div className="flex items-center space-x-2">
            <span>Press <kbd className="rounded bg-zinc-800 px-1.5 py-0.5 font-mono text-[10px] text-zinc-300">Enter ⏎</kbd> to run</span>
            <span>•</span>
            <span><kbd className="rounded bg-zinc-800 px-1.5 py-0.5 font-mono text-[10px] text-zinc-300">Shift + Enter</kbd> for newline</span>
          </div>
          <div className="flex items-center space-x-1 text-zinc-400">
            <span>FastAPI + SQLite WAL</span>
            <ArrowUpRight className="h-3 w-3 text-indigo-400" />
          </div>
        </div>
      </div>
    </div>
  );
};

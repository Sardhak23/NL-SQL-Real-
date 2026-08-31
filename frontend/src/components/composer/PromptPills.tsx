import React from 'react';
import { Sparkles } from 'lucide-react';

interface PromptPillsProps {
  onSelectPrompt: (prompt: string) => void;
  disabled?: boolean;
}

const QUICK_PILLS = [
  'Top 5 categories by revenue in 2024',
  'Monthly revenue trend 2024',
  'Customer Lifetime Value across loyalty tiers',
  'Low stock inventory alert (<15 units)',
  'Average discount by order status',
  'Repeat purchase rate of customers',
];

export const PromptPills: React.FC<PromptPillsProps> = ({ onSelectPrompt, disabled }) => {
  return (
    <div className="flex items-center space-x-2 overflow-x-auto py-1 scrollbar-none">
      <div className="flex items-center space-x-1 text-xs text-indigo-400 font-medium shrink-0">
        <Sparkles className="h-3.5 w-3.5" />
        <span>Suggestions:</span>
      </div>
      <div className="flex items-center space-x-2">
        {QUICK_PILLS.map((pill) => (
          <button
            key={pill}
            onClick={() => onSelectPrompt(pill)}
            disabled={disabled}
            className="shrink-0 rounded-full border border-zinc-800 bg-zinc-900/80 px-3 py-1 text-xs font-normal text-zinc-300 transition-all hover:border-indigo-500/60 hover:bg-zinc-850 hover:text-white disabled:opacity-50"
          >
            {pill}
          </button>
        ))}
      </div>
    </div>
  );
};

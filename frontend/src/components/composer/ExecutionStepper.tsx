import React from 'react';
import {
  CheckCircle2,
  Loader2,
  AlertCircle,
  Database,
  Code2,
  ShieldCheck,
  Zap,
  Sparkles,
  RefreshCw,
} from 'lucide-react';
import { ExecutionStep } from '../../types';

interface ExecutionStepperProps {
  steps: ExecutionStep[];
  currentStepIndex: number;
  isExecuting: boolean;
}

export const ExecutionStepper: React.FC<ExecutionStepperProps> = ({
  steps,
  currentStepIndex,
  isExecuting,
}) => {
  if (!isExecuting && steps.every((s) => s.status === 'pending')) {
    return null;
  }

  const getStepIcon = (id: string, status: string) => {
    if (status === 'running') {
      return <Loader2 className="h-3.5 w-3.5 animate-spin text-indigo-400" />;
    }
    if (status === 'completed') {
      return <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />;
    }
    if (status === 'error') {
      return <AlertCircle className="h-3.5 w-3.5 text-rose-400" />;
    }

    switch (id) {
      case 'linking':
        return <Database className="h-3.5 w-3.5 text-zinc-500" />;
      case 'generation':
        return <Code2 className="h-3.5 w-3.5 text-zinc-500" />;
      case 'safety':
        return <ShieldCheck className="h-3.5 w-3.5 text-zinc-500" />;
      case 'execution':
        return <Zap className="h-3.5 w-3.5 text-zinc-500" />;
      case 'correction':
        return <RefreshCw className="h-3.5 w-3.5 text-zinc-500" />;
      case 'insights':
        return <Sparkles className="h-3.5 w-3.5 text-zinc-500" />;
      default:
        return <Database className="h-3.5 w-3.5 text-zinc-500" />;
    }
  };

  return (
    <div className="rounded-xl border border-zinc-800/80 bg-zinc-950/80 p-4 shadow-xl backdrop-blur-xl">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="h-2 w-2 rounded-full bg-indigo-500 animate-ping" />
          <span className="text-xs font-semibold uppercase tracking-wider text-indigo-400">
            Pipeline Execution Lifecycle
          </span>
        </div>
        <span className="text-[11px] font-mono text-zinc-500">
          Stage {Math.min(currentStepIndex + 1, steps.length)} of {steps.length}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 md:grid-cols-3 lg:grid-cols-6">
        {steps.map((step, idx) => {
          const isCurrent = idx === currentStepIndex && isExecuting;
          const isDone = step.status === 'completed';
          const isErr = step.status === 'error';

          return (
            <div
              key={step.id}
              className={`flex flex-col justify-between rounded-lg border p-2.5 transition-all ${
                isCurrent
                  ? 'border-indigo-500/60 bg-indigo-950/30 ring-1 ring-indigo-500/30'
                  : isDone
                  ? 'border-emerald-900/40 bg-emerald-950/20'
                  : isErr
                  ? 'border-rose-900/40 bg-rose-950/20'
                  : 'border-zinc-850 bg-zinc-900/40 opacity-60'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center space-x-1.5">
                  {getStepIcon(step.id, step.status)}
                  <span className="text-[11px] font-semibold text-zinc-200 truncate">
                    {step.name}
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between text-[10px] text-zinc-400">
                <span className="truncate">{step.details || step.description}</span>
                {step.durationMs !== undefined && (
                  <span className="font-mono text-emerald-400 shrink-0 ml-1">
                    {step.durationMs.toFixed(0)}ms
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import {
  Copy,
  Check,
  Zap,
  Clock,
  Database,
  RefreshCw,
  FileCode,
  CheckCircle2,
  AlertTriangle,
  Info,
} from 'lucide-react';
import { copyToClipboard } from '../../utils/export';

interface SqlInspectorProps {
  sql: string;
  explanation: string;
  sqlBreakdown?: {
    select?: string;
    from?: string;
    join?: string[];
    where?: string;
    group_by?: string;
    order_by?: string;
    limit?: string;
  };
  executionTimeMs: number;
  rowCount: number;
  correctionAttempts: number;
  correctionLog?: Array<{
    attempt: number;
    error: string;
    attempted_sql: string;
    correction: string;
  }>;
}

export const SqlInspector: React.FC<SqlInspectorProps> = ({
  sql,
  explanation,
  sqlBreakdown,
  executionTimeMs,
  rowCount,
  correctionAttempts,
  correctionLog,
}) => {
  const [copied, setCopied] = useState(false);
  const [showCorrectionLog, setShowCorrectionLog] = useState(false);

  const handleCopy = async () => {
    const success = await copyToClipboard(sql);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-4 rounded-xl border border-zinc-800/80 bg-zinc-950/60 p-5 shadow-lg backdrop-blur-xl">
      {/* Execution Diagnostics Stat Pills */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {/* Execution Time */}
        <div className="flex items-center space-x-2.5 rounded-lg border border-zinc-800 bg-zinc-900/60 p-2.5">
          <div className="rounded-md bg-emerald-500/10 p-1.5 text-emerald-400">
            <Zap className="h-4 w-4" />
          </div>
          <div>
            <div className="text-[10px] uppercase font-medium text-zinc-500">Latency</div>
            <div className="font-mono text-xs font-semibold text-emerald-400">
              {executionTimeMs.toFixed(1)} ms
            </div>
          </div>
        </div>

        {/* Rows Returned */}
        <div className="flex items-center space-x-2.5 rounded-lg border border-zinc-800 bg-zinc-900/60 p-2.5">
          <div className="rounded-md bg-indigo-500/10 p-1.5 text-indigo-400">
            <Database className="h-4 w-4" />
          </div>
          <div>
            <div className="text-[10px] uppercase font-medium text-zinc-500">Dataset Rows</div>
            <div className="font-mono text-xs font-semibold text-zinc-200">
              {rowCount.toLocaleString()} rows
            </div>
          </div>
        </div>

        {/* Database Engine */}
        <div className="flex items-center space-x-2.5 rounded-lg border border-zinc-800 bg-zinc-900/60 p-2.5">
          <div className="rounded-md bg-purple-500/10 p-1.5 text-purple-400">
            <FileCode className="h-4 w-4" />
          </div>
          <div>
            <div className="text-[10px] uppercase font-medium text-zinc-500">DB Dialect</div>
            <div className="font-mono text-xs font-semibold text-purple-300">
              SQLite (WAL)
            </div>
          </div>
        </div>

        {/* Self-Correction Retries */}
        <div className="flex items-center space-x-2.5 rounded-lg border border-zinc-800 bg-zinc-900/60 p-2.5">
          <div
            className={`rounded-md p-1.5 ${
              correctionAttempts > 0
                ? 'bg-amber-500/10 text-amber-400'
                : 'bg-emerald-500/10 text-emerald-400'
            }`}
          >
            <RefreshCw className="h-4 w-4" />
          </div>
          <div>
            <div className="text-[10px] uppercase font-medium text-zinc-500">Self-Correction</div>
            <div
              className={`font-mono text-xs font-semibold ${
                correctionAttempts > 0 ? 'text-amber-400' : 'text-emerald-400'
              }`}
            >
              {correctionAttempts === 0 ? '0 Retries (Clean)' : `${correctionAttempts} Retries Headed`}
            </div>
          </div>
        </div>
      </div>

      {/* Self-Correction Warning/Log banner if attempts > 0 */}
      {correctionAttempts > 0 && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-950/20 p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs font-semibold text-amber-300">
              <AlertTriangle className="h-4 w-4 text-amber-400" />
              <span>
                Self-Correction Triggered: Query repaired successfully in {correctionAttempts} iteration(s).
              </span>
            </div>
            {correctionLog && correctionLog.length > 0 && (
              <button
                onClick={() => setShowCorrectionLog(!showCorrectionLog)}
                className="text-[11px] font-medium text-amber-400 underline hover:text-amber-300"
              >
                {showCorrectionLog ? 'Hide Trace' : 'View Trace'}
              </button>
            )}
          </div>
          {showCorrectionLog && correctionLog && (
            <div className="mt-2.5 space-y-2 border-t border-amber-500/20 pt-2 text-xs">
              {correctionLog.map((log, idx) => (
                <div key={idx} className="rounded bg-zinc-900/80 p-2 font-mono text-[11px]">
                  <div className="text-rose-400">Attempt {log.attempt} Error: {log.error}</div>
                  <div className="text-zinc-500">Failed SQL: {log.attempted_sql}</div>
                  <div className="text-emerald-400">Fixed: {log.correction}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Syntax-Highlighted SQL Code Block */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs font-semibold text-zinc-300">
          <div className="flex items-center space-x-1.5">
            <FileCode className="h-3.5 w-3.5 text-indigo-400" />
            <span>Generated SQLite Query:</span>
          </div>
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 rounded-md border border-zinc-800 bg-zinc-900 px-2.5 py-1 text-xs font-medium text-zinc-300 transition-colors hover:border-indigo-500/50 hover:bg-zinc-800 hover:text-white"
          >
            {copied ? (
              <>
                <Check className="h-3 w-3 text-emerald-400" />
                <span className="text-emerald-400">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="h-3 w-3" />
                <span>Copy SQL</span>
              </>
            )}
          </button>
        </div>

        {/* Code Container */}
        <div className="relative rounded-lg border border-zinc-800 bg-zinc-900/90 p-4 font-mono text-xs text-indigo-200 overflow-x-auto shadow-inner">
          <pre className="leading-relaxed whitespace-pre-wrap">{sql}</pre>
        </div>
      </div>

      {/* Plain-English SQL Explanation Card */}
      <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 space-y-2">
        <div className="flex items-center space-x-1.5 text-xs font-semibold text-zinc-200">
          <Info className="h-3.5 w-3.5 text-indigo-400" />
          <span>Plain-English Logic Breakdown:</span>
        </div>
        <p className="text-xs text-zinc-300 leading-relaxed">{explanation}</p>

        {/* Clause by Clause Breakdown if available */}
        {sqlBreakdown && (
          <div className="grid grid-cols-1 gap-2 pt-2 sm:grid-cols-2 text-xs">
            {sqlBreakdown.select && (
              <div className="rounded border border-zinc-800/80 bg-zinc-950/60 p-2">
                <span className="font-mono font-semibold text-indigo-400">SELECT: </span>
                <span className="text-zinc-300">{sqlBreakdown.select}</span>
              </div>
            )}
            {sqlBreakdown.from && (
              <div className="rounded border border-zinc-800/80 bg-zinc-950/60 p-2">
                <span className="font-mono font-semibold text-indigo-400">FROM: </span>
                <span className="text-zinc-300">{sqlBreakdown.from}</span>
              </div>
            )}
            {sqlBreakdown.where && (
              <div className="rounded border border-zinc-800/80 bg-zinc-950/60 p-2">
                <span className="font-mono font-semibold text-indigo-400">WHERE: </span>
                <span className="text-zinc-300">{sqlBreakdown.where}</span>
              </div>
            )}
            {sqlBreakdown.group_by && (
              <div className="rounded border border-zinc-800/80 bg-zinc-950/60 p-2">
                <span className="font-mono font-semibold text-indigo-400">GROUP BY: </span>
                <span className="text-zinc-300">{sqlBreakdown.group_by}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

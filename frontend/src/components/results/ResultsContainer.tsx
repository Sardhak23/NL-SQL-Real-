import React, { useState } from 'react';
import {
  BarChart2,
  Table,
  Code2,
  Sparkles,
  ArrowRight,
  AlertCircle,
} from 'lucide-react';
import { QueryResponse } from '../../types';
import { ExecutiveSummary } from './ExecutiveSummary';
import { DataCharts } from './DataCharts';
import { DataTable } from './DataTable';
import { SqlInspector } from './SqlInspector';

interface ResultsContainerProps {
  response: QueryResponse | null;
  onSelectFollowup: (question: string) => void;
}

export const ResultsContainer: React.FC<ResultsContainerProps> = ({
  response,
  onSelectFollowup,
}) => {
  const [activeTab, setActiveTab] = useState<'insights' | 'table' | 'sql'>('insights');

  if (!response) {
    return (
      <div className="flex min-h-[380px] flex-col items-center justify-center rounded-2xl border border-zinc-800/80 bg-zinc-950/40 p-8 text-center backdrop-blur-xl">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-400 ring-1 ring-indigo-500/20 mb-4">
          <Sparkles className="h-7 w-7 animate-pulse-subtle" />
        </div>
        <h3 className="text-base font-semibold text-zinc-200">
          Ready to Analyze 500,000+ Orders
        </h3>
        <p className="mt-1 max-w-md text-xs text-zinc-400 leading-relaxed">
          Ask any question above or choose a suggested starter query to generate schema-linked SQL, interactive visual charts, and executive insights.
        </p>
      </div>
    );
  }

  // Error boundary state
  if (response.error || !response.success) {
    return (
      <div className="rounded-2xl border border-rose-900/50 bg-rose-950/20 p-6 backdrop-blur-xl">
        <div className="flex items-start space-x-3">
          <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-rose-300">
              Query Execution Intercepted
            </h3>
            <p className="text-xs text-rose-200/90 leading-relaxed">
              {response.error || 'The NL-to-SQL engine was unable to process this inquiry.'}
            </p>
            {response.sql && (
              <div className="rounded bg-zinc-900/90 p-3 font-mono text-xs text-rose-300">
                {response.sql}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 3-Tab Header Navigation */}
      <div className="flex items-center justify-between border-b border-zinc-800/80 pb-2">
        <div className="flex items-center space-x-2">
          {/* Tab 1: Executive Insights & Charts */}
          <button
            onClick={() => setActiveTab('insights')}
            className={`flex items-center space-x-2 rounded-lg px-3.5 py-2 text-xs font-semibold transition-all ${
              activeTab === 'insights'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20'
                : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
            }`}
          >
            <BarChart2 className="h-4 w-4" />
            <span>Executive Insights & Charts</span>
          </button>

          {/* Tab 2: Interactive Data Table */}
          <button
            onClick={() => setActiveTab('table')}
            className={`flex items-center space-x-2 rounded-lg px-3.5 py-2 text-xs font-semibold transition-all ${
              activeTab === 'table'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20'
                : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
            }`}
          >
            <Table className="h-4 w-4" />
            <span>Data Table</span>
            <span className="ml-1 rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] font-mono">
              {response.row_count}
            </span>
          </button>

          {/* Tab 3: SQL Inspector */}
          <button
            onClick={() => setActiveTab('sql')}
            className={`flex items-center space-x-2 rounded-lg px-3.5 py-2 text-xs font-semibold transition-all ${
              activeTab === 'sql'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20'
                : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
            }`}
          >
            <Code2 className="h-4 w-4" />
            <span>SQL Inspector</span>
            <span className="ml-1 rounded bg-emerald-950/60 text-emerald-400 px-1.5 py-0.5 text-[10px] font-mono">
              {response.execution_time_ms.toFixed(0)}ms
            </span>
          </button>
        </div>
      </div>

      {/* Tab Panels */}
      {activeTab === 'insights' && (
        <div className="space-y-4">
          <ExecutiveSummary summary={response.executive_summary} />
          {response.chart_spec && response.chart_spec.is_plottable !== false && (
            <DataCharts
              spec={response.chart_spec}
              rows={response.rows}
              columns={response.columns}
            />
          )}
        </div>
      )}

      {activeTab === 'table' && (
        <DataTable
          rows={response.rows}
          columns={response.columns}
          question={response.question}
        />
      )}

      {activeTab === 'sql' && (
        <SqlInspector
          sql={response.sql}
          explanation={response.explanation}
          sqlBreakdown={response.sql_breakdown}
          executionTimeMs={response.execution_time_ms}
          rowCount={response.row_count}
          correctionAttempts={response.correction_attempts}
          correctionLog={response.correction_log}
        />
      )}

      {/* Suggested Follow-up Prompts Section */}
      {response.suggested_followups && response.suggested_followups.length > 0 && (
        <div className="rounded-xl border border-zinc-800/80 bg-zinc-950/60 p-4 backdrop-blur-xl">
          <div className="mb-2 flex items-center space-x-1.5 text-xs font-semibold text-zinc-300">
            <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
            <span>Recommended Follow-up Inquiries:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {response.suggested_followups.map((followup, idx) => (
              <button
                key={idx}
                onClick={() => onSelectFollowup(followup)}
                className="flex items-center space-x-1.5 rounded-lg border border-zinc-800 bg-zinc-900/80 px-3 py-1.5 text-xs text-zinc-300 transition-all hover:border-indigo-500/60 hover:bg-zinc-850 hover:text-white group"
              >
                <span>{followup}</span>
                <ArrowRight className="h-3 w-3 text-zinc-500 transition-transform group-hover:translate-x-0.5 group-hover:text-indigo-400" />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

import React from 'react';
import { Database, Sparkles, Activity, RefreshCw, Trash2, Cpu, ShieldCheck } from 'lucide-react';
import { Dialect } from '../../types';

interface HeaderProps {
  dialect: Dialect;
  onDialectChange: (dialect: Dialect) => void;
  onClearHistory: () => void;
  onRefreshSchema: () => void;
  isRefreshing: boolean;
  totalOrders?: number;
  totalTables?: number;
  lastLatencyMs?: number;
  isOnline: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  dialect,
  onDialectChange,
  onClearHistory,
  onRefreshSchema,
  isRefreshing,
  totalOrders = 500000,
  totalTables = 8,
  lastLatencyMs = 42.8,
  isOnline = true,
}) => {
  return (
    <header className="sticky top-0 z-30 flex items-center justify-between border-b border-zinc-800/80 bg-zinc-950/90 px-5 py-3 backdrop-blur-xl">
      {/* Brand & Title */}
      <div className="flex items-center space-x-3.5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-purple-600 shadow-lg shadow-indigo-500/20 ring-1 ring-white/20">
          <Sparkles className="h-5 w-5 text-white animate-pulse-subtle" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-base font-semibold tracking-tight text-white">
              NL-SQL Analytics Copilot
            </h1>
            <span className="rounded-full border border-indigo-500/30 bg-indigo-500/10 px-2 py-0.5 text-[10px] font-medium tracking-wide text-indigo-400">
              v2.0 Enterprise
            </span>
          </div>
          <p className="text-xs text-zinc-400">
            Autonomous Business Intelligence & Self-Correcting SQL Engine
          </p>
        </div>
      </div>

      {/* Metadata Badges & Live Status */}
      <div className="hidden items-center space-x-3 md:flex">
        {/* Database Status Badge */}
        <div className="flex items-center space-x-2 rounded-lg border border-zinc-800 bg-zinc-900/80 px-3 py-1.5 text-xs text-zinc-300 shadow-sm">
          <Database className="h-3.5 w-3.5 text-indigo-400" />
          <span className="font-mono text-zinc-200">ecommerce.db</span>
          <span className="text-zinc-500">•</span>
          <span className="text-zinc-400">
            {totalOrders.toLocaleString()}+ orders ({totalTables} tables)
          </span>
        </div>

        {/* Engine Liveness Pill */}
        <div className="flex items-center space-x-2 rounded-lg border border-zinc-800 bg-zinc-900/80 px-3 py-1.5 text-xs text-zinc-300">
          <div className="relative flex h-2 w-2">
            <span
              className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 ${
                isOnline ? 'bg-emerald-400' : 'bg-amber-400'
              }`}
            />
            <span
              className={`relative inline-flex h-2 w-2 rounded-full ${
                isOnline ? 'bg-emerald-500' : 'bg-amber-500'
              }`}
            />
          </div>
          <Cpu className="h-3.5 w-3.5 text-zinc-400" />
          <span className="text-zinc-200 font-medium">
            {isOnline ? 'Gemini 1.5 + SQLite' : 'Offline Mode'}
          </span>
          {lastLatencyMs !== undefined && (
            <>
              <span className="text-zinc-500">•</span>
              <div className="flex items-center space-x-1 text-zinc-400">
                <Activity className="h-3 w-3 text-emerald-400" />
                <span className="font-mono">{lastLatencyMs.toFixed(0)}ms</span>
              </div>
            </>
          )}
        </div>

        {/* Security Guardrail Tag */}
        <div className="flex items-center space-x-1.5 rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-2.5 py-1.5 text-xs font-medium text-emerald-400">
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>Read-Only AST Guard</span>
        </div>
      </div>

      {/* Action Controls */}
      <div className="flex items-center space-x-2">
        {/* Dialect Selector */}
        <select
          value={dialect}
          onChange={(e) => onDialectChange(e.target.value as Dialect)}
          aria-label="SQL Dialect"
          className="rounded-lg border border-zinc-800 bg-zinc-900 px-2.5 py-1.5 text-xs font-medium text-zinc-300 transition-colors hover:border-zinc-700 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="sqlite">SQLite (Optimized)</option>
          <option value="postgres">PostgreSQL</option>
          <option value="mysql">MySQL</option>
          <option value="snowflake">Snowflake</option>
        </select>

        {/* Refresh Schema Button */}
        <button
          onClick={onRefreshSchema}
          disabled={isRefreshing}
          title="Refresh Database Schema"
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-900 text-zinc-400 transition-colors hover:border-zinc-700 hover:text-zinc-200 disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin text-indigo-400' : ''}`} />
        </button>

        {/* Clear History Button */}
        <button
          onClick={onClearHistory}
          title="Clear Conversation History"
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-900 text-zinc-400 transition-colors hover:border-red-900/50 hover:bg-red-950/20 hover:text-red-400"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>
    </header>
  );
};

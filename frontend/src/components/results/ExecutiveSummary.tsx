import React from 'react';
import { Sparkles, TrendingUp, TrendingDown, Minus, CheckCircle, Lightbulb } from 'lucide-react';
import { ExecutiveSummary as IExecutiveSummary } from '../../types';

interface ExecutiveSummaryProps {
  summary: IExecutiveSummary;
}

export const ExecutiveSummary: React.FC<ExecutiveSummaryProps> = ({ summary }) => {
  return (
    <div className="space-y-4 rounded-xl border border-zinc-800/80 bg-zinc-950/60 p-5 shadow-lg backdrop-blur-xl">
      {/* AI Headline Banner */}
      <div className="flex items-start space-x-3 rounded-lg border border-indigo-500/20 bg-gradient-to-r from-indigo-950/40 via-purple-950/20 to-transparent p-3.5">
        <div className="rounded-lg bg-indigo-500/20 p-1.5 text-indigo-400 shrink-0">
          <Sparkles className="h-4 w-4" />
        </div>
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-indigo-400">
            Executive Summary
          </div>
          <p className="mt-0.5 text-sm font-medium text-zinc-100 leading-snug">
            {summary.headline}
          </p>
        </div>
      </div>

      {/* KPI Highlights Cards */}
      {summary.key_metrics && summary.key_metrics.length > 0 && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {summary.key_metrics.map((metric, idx) => {
            const isUp = metric.trend === 'up';
            const isDown = metric.trend === 'down';

            return (
              <div
                key={idx}
                className="flex flex-col justify-between rounded-lg border border-zinc-800 bg-zinc-900/60 p-3"
              >
                <span className="text-[11px] font-medium text-zinc-400 truncate">
                  {metric.label}
                </span>
                <div className="mt-1 flex items-baseline justify-between">
                  <span className="text-lg font-bold tracking-tight text-white font-mono">
                    {metric.value}
                  </span>
                  {metric.change && (
                    <div
                      className={`flex items-center space-x-0.5 text-xs font-semibold ${
                        isUp
                          ? 'text-emerald-400'
                          : isDown
                          ? 'text-rose-400'
                          : 'text-zinc-400'
                      }`}
                    >
                      {isUp && <TrendingUp className="h-3 w-3" />}
                      {isDown && <TrendingDown className="h-3 w-3" />}
                      {!isUp && !isDown && <Minus className="h-3 w-3" />}
                      <span>{metric.change}</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Bulleted Insights */}
      {summary.bullet_points && summary.bullet_points.length > 0 && (
        <div className="space-y-1.5 pt-1">
          <div className="text-xs font-semibold text-zinc-300">Key Analytical Findings:</div>
          <ul className="space-y-1.5 text-xs text-zinc-300">
            {summary.bullet_points.map((point, idx) => (
              <li key={idx} className="flex items-start space-x-2">
                <CheckCircle className="mt-0.5 h-3.5 w-3.5 text-emerald-400 shrink-0" />
                <span className="leading-relaxed">{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Actionable Recommendations */}
      {summary.actionable_recommendations && summary.actionable_recommendations.length > 0 && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-950/20 p-3 space-y-1.5">
          <div className="flex items-center space-x-1.5 text-xs font-semibold text-amber-400">
            <Lightbulb className="h-3.5 w-3.5" />
            <span>Actionable Next Steps:</span>
          </div>
          <ul className="space-y-1 text-xs text-amber-200/90">
            {summary.actionable_recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start space-x-2">
                <span className="text-amber-400 font-bold">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

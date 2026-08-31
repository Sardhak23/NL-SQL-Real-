import React, { useState } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import {
  BarChart3,
  LineChart as LineChartIcon,
  PieChart as PieChartIcon,
  TrendingUp,
  AlignLeft,
  ScatterChart as ScatterIcon,
} from 'lucide-react';
import { ChartSpec, ChartType } from '../../types';
import { formatCurrency, formatNumber } from '../../utils/formatters';

interface DataChartsProps {
  spec: ChartSpec;
  rows: Record<string, any>[];
  columns: string[];
}

const PALETTE = [
  '#6366f1', // Indigo
  '#8b5cf6', // Violet
  '#10b981', // Emerald
  '#f59e0b', // Amber
  '#06b6d4', // Cyan
  '#ec4899', // Pink
  '#3b82f6', // Blue
  '#14b8a6', // Teal
];

export const DataCharts: React.FC<DataChartsProps> = ({ spec, rows, columns }) => {
  const [selectedChartType, setSelectedChartType] = useState<ChartType>(
    spec.chart_type || 'bar'
  );

  if (!rows || rows.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-950/40 text-xs text-zinc-500">
        No plottable rows returned for this query.
      </div>
    );
  }

  // Automatic axis inference fallback
  const xAxisKey = spec.x_axis || columns[0] || 'category';
  const yAxisKey = spec.y_axis || (columns.length > 1 ? columns[1] : columns[0]);
  const secondaryKey = spec.secondary_y_axis;

  // Custom Dark Tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-xl border border-zinc-700 bg-zinc-900/95 p-3 shadow-2xl backdrop-blur-xl">
          <div className="mb-1 text-xs font-semibold text-zinc-200">{label}</div>
          {payload.map((entry: any, index: number) => {
            const isCurrency =
              entry.name.toLowerCase().includes('revenue') ||
              entry.name.toLowerCase().includes('price') ||
              entry.name.toLowerCase().includes('spend') ||
              entry.name.toLowerCase().includes('margin') ||
              entry.name.toLowerCase().includes('cost') ||
              entry.name.toLowerCase().includes('total');

            const val = typeof entry.value === 'number'
              ? isCurrency
                ? formatCurrency(entry.value)
                : formatNumber(entry.value)
              : entry.value;

            return (
              <div key={index} className="flex items-center space-x-2 text-xs">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: entry.color || PALETTE[index % PALETTE.length] }}
                />
                <span className="text-zinc-400 capitalize">{entry.name.replace(/_/g, ' ')}:</span>
                <span className="font-mono font-semibold text-white">{val}</span>
              </div>
            );
          })}
        </div>
      );
    }
    return null;
  };

  const renderChart = () => {
    switch (selectedChartType) {
      case 'horizontal_bar':
        return (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart
              data={rows}
              layout="vertical"
              margin={{ top: 10, right: 30, left: 40, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={false} />
              <XAxis
                type="number"
                stroke="#71717a"
                tick={{ fontSize: 11 }}
                tickFormatter={(val) => formatNumber(val)}
              />
              <YAxis
                type="category"
                dataKey={xAxisKey}
                stroke="#71717a"
                tick={{ fontSize: 11 }}
                width={120}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: '11px', color: '#a1a1aa' }} />
              <Bar dataKey={yAxisKey} fill="#6366f1" radius={[0, 4, 4, 0]} name={yAxisKey} />
              {secondaryKey && (
                <Bar dataKey={secondaryKey} fill="#8b5cf6" radius={[0, 4, 4, 0]} name={secondaryKey} />
              )}
            </BarChart>
          </ResponsiveContainer>
        );

      case 'line':
        return (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={rows} margin={{ top: 10, right: 30, left: 20, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis dataKey={xAxisKey} stroke="#71717a" tick={{ fontSize: 11 }} />
              <YAxis
                stroke="#71717a"
                tick={{ fontSize: 11 }}
                tickFormatter={(val) => formatNumber(val)}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: '11px', color: '#a1a1aa' }} />
              <Line
                type="monotone"
                dataKey={yAxisKey}
                stroke="#6366f1"
                strokeWidth={2.5}
                dot={{ r: 4, fill: '#6366f1' }}
                activeDot={{ r: 6 }}
                name={yAxisKey}
              />
              {secondaryKey && (
                <Line
                  type="monotone"
                  dataKey={secondaryKey}
                  stroke="#10b981"
                  strokeWidth={2}
                  strokeDasharray="4 4"
                  name={secondaryKey}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        );

      case 'area':
        return (
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={rows} margin={{ top: 10, right: 30, left: 20, bottom: 10 }}>
              <defs>
                <linearGradient id="colorY" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                </linearGradient>
                {secondaryKey && (
                  <linearGradient id="colorSec" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                  </linearGradient>
                )}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis dataKey={xAxisKey} stroke="#71717a" tick={{ fontSize: 11 }} />
              <YAxis
                stroke="#71717a"
                tick={{ fontSize: 11 }}
                tickFormatter={(val) => formatNumber(val)}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: '11px', color: '#a1a1aa' }} />
              <Area
                type="monotone"
                dataKey={yAxisKey}
                stroke="#6366f1"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorY)"
                name={yAxisKey}
              />
              {secondaryKey && (
                <Area
                  type="monotone"
                  dataKey={secondaryKey}
                  stroke="#10b981"
                  strokeWidth={1.5}
                  fillOpacity={1}
                  fill="url(#colorSec)"
                  name={secondaryKey}
                />
              )}
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'pie':
      case 'donut':
        return (
          <ResponsiveContainer width="100%" height={320}>
            <PieChart>
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: '11px', color: '#a1a1aa' }} />
              <Pie
                data={rows}
                dataKey={yAxisKey}
                nameKey={xAxisKey}
                cx="50%"
                cy="50%"
                innerRadius={selectedChartType === 'donut' ? 65 : 0}
                outerRadius={105}
                paddingAngle={selectedChartType === 'donut' ? 4 : 0}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              >
                {rows.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={PALETTE[index % PALETTE.length]} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        );

      case 'scatter':
        return (
          <ResponsiveContainer width="100%" height={320}>
            <ScatterChart margin={{ top: 10, right: 30, left: 20, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis
                dataKey={xAxisKey}
                stroke="#71717a"
                name={xAxisKey}
                tick={{ fontSize: 11 }}
              />
              <YAxis
                dataKey={yAxisKey}
                stroke="#71717a"
                name={yAxisKey}
                tick={{ fontSize: 11 }}
                tickFormatter={(val) => formatNumber(val)}
              />
              <Tooltip content={<CustomTooltip />} />
              <Scatter name="Data Points" data={rows} fill="#6366f1" />
            </ScatterChart>
          </ResponsiveContainer>
        );

      case 'bar':
      default:
        return (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={rows} margin={{ top: 10, right: 30, left: 20, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
              <XAxis dataKey={xAxisKey} stroke="#71717a" tick={{ fontSize: 11 }} />
              <YAxis
                stroke="#71717a"
                tick={{ fontSize: 11 }}
                tickFormatter={(val) => formatNumber(val)}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: '11px', color: '#a1a1aa' }} />
              <Bar dataKey={yAxisKey} fill="#6366f1" radius={[4, 4, 0, 0]} name={yAxisKey} />
              {secondaryKey && (
                <Bar dataKey={secondaryKey} fill="#8b5cf6" radius={[4, 4, 0, 0]} name={secondaryKey} />
              )}
            </BarChart>
          </ResponsiveContainer>
        );
    }
  };

  return (
    <div className="space-y-4 rounded-xl border border-zinc-800/80 bg-zinc-950/60 p-5 shadow-lg backdrop-blur-xl">
      {/* Chart Header & Type Switcher */}
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h3 className="text-sm font-semibold text-white">{spec.title || 'Data Visualization'}</h3>
          {spec.description && (
            <p className="text-xs text-zinc-400">{spec.description}</p>
          )}
        </div>

        {/* Toolbar Switcher */}
        <div className="flex items-center space-x-1 rounded-lg border border-zinc-800 bg-zinc-900/80 p-1">
          <button
            onClick={() => setSelectedChartType('bar')}
            title="Vertical Bar Chart"
            className={`rounded px-2 py-1 text-xs font-medium transition-colors ${
              selectedChartType === 'bar'
                ? 'bg-zinc-800 text-white'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <BarChart3 className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setSelectedChartType('horizontal_bar')}
            title="Horizontal Bar Chart"
            className={`rounded px-2 py-1 text-xs font-medium transition-colors ${
              selectedChartType === 'horizontal_bar'
                ? 'bg-zinc-800 text-white'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <AlignLeft className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setSelectedChartType('line')}
            title="Line Trend Chart"
            className={`rounded px-2 py-1 text-xs font-medium transition-colors ${
              selectedChartType === 'line'
                ? 'bg-zinc-800 text-white'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <LineChartIcon className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setSelectedChartType('area')}
            title="Area Chart"
            className={`rounded px-2 py-1 text-xs font-medium transition-colors ${
              selectedChartType === 'area'
                ? 'bg-zinc-800 text-white'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <TrendingUp className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setSelectedChartType('donut')}
            title="Donut / Pie Chart"
            className={`rounded px-2 py-1 text-xs font-medium transition-colors ${
              selectedChartType === 'donut' || selectedChartType === 'pie'
                ? 'bg-zinc-800 text-white'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <PieChartIcon className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setSelectedChartType('scatter')}
            title="Scatter Correlation Plot"
            className={`rounded px-2 py-1 text-xs font-medium transition-colors ${
              selectedChartType === 'scatter'
                ? 'bg-zinc-800 text-white'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <ScatterIcon className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Render Chart Container */}
      <div className="pt-2">{renderChart()}</div>
    </div>
  );
};

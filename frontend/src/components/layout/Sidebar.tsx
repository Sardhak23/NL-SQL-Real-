import React, { useState, useMemo } from 'react';
import {
  Table2,
  ChevronDown,
  ChevronRight,
  Search,
  Key,
  Link2,
  History,
  Clock,
  Zap,
  Sparkles,
  Layers,
  BarChart3,
  Users,
  Package,
  TrendingUp,
  Info,
} from 'lucide-react';
import { SchemaResponse, TableMetadata, HistoryItem } from '../../types';

interface SidebarProps {
  schema: SchemaResponse | null;
  isLoadingSchema: boolean;
  history: HistoryItem[];
  onSelectHistory: (item: HistoryItem) => void;
  onSelectPrompt: (prompt: string) => void;
  onOpenTableDetails: (table: TableMetadata) => void;
}

const STARTER_PROMPTS = [
  {
    category: 'Revenue & Sales Trends',
    icon: TrendingUp,
    color: 'text-indigo-400',
    prompts: [
      'What are the top 5 product categories by revenue in 2024?',
      'Monthly sales revenue trend with order count for 2024',
      'Compare quarterly revenue between 2023 and 2024',
    ],
  },
  {
    category: 'Customer & CLV Analytics',
    icon: Users,
    color: 'text-emerald-400',
    prompts: [
      'What is the Customer Lifetime Value (CLV) distribution across loyalty tiers?',
      'Show the average order value (AOV) by customer segment',
      'Calculate customer repeat purchase rate (customers with >1 order vs total)',
    ],
  },
  {
    category: 'Inventory & Operations',
    icon: Package,
    color: 'text-amber-400',
    prompts: [
      'Find products that have less than 15 units in stock along with warehouse location',
      'What is the total quantity of inventory currently stored in each warehouse?',
      'Identify products with high review ratings (>= 4.5) but low inventory (< 25)',
    ],
  },
  {
    category: 'Advanced & Window KPIs',
    icon: BarChart3,
    color: 'text-purple-400',
    prompts: [
      'Rank product categories by total profit margin',
      'Find the 3-month moving average of monthly sales revenue in 2024',
      'Find the top 5 suppliers whose products generated the highest net profit',
    ],
  },
];

export const Sidebar: React.FC<SidebarProps> = ({
  schema,
  isLoadingSchema,
  history,
  onSelectHistory,
  onSelectPrompt,
  onOpenTableDetails,
}) => {
  const [activeTab, setActiveTab] = useState<'schema' | 'history' | 'starters'>('schema');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedTables, setExpandedTables] = useState<Record<string, boolean>>({
    orders: true,
    products: true,
  });

  const toggleTable = (tableName: string) => {
    setExpandedTables((prev) => ({
      ...prev,
      [tableName]: !prev[tableName],
    }));
  };

  // Filtered tables based on search query
  const filteredTables = useMemo(() => {
    if (!schema?.tables) return [];
    if (!searchQuery.trim()) return schema.tables;

    const query = searchQuery.toLowerCase();
    return schema.tables.filter((table) => {
      const matchName = table.name.toLowerCase().includes(query);
      const matchDesc = table.description?.toLowerCase().includes(query) ?? false;
      const matchCol = table.columns.some((c) =>
        c.name.toLowerCase().includes(query) || c.type.toLowerCase().includes(query)
      );
      return matchName || matchDesc || matchCol;
    });
  }, [schema, searchQuery]);

  return (
    <aside className="flex h-full w-80 flex-col border-r border-zinc-800/80 bg-zinc-950/70 backdrop-blur-xl">
      {/* Tab Switcher */}
      <div className="flex border-b border-zinc-800/80 p-2 gap-1 bg-zinc-950/40">
        <button
          onClick={() => setActiveTab('schema')}
          className={`flex flex-1 items-center justify-center space-x-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-all ${
            activeTab === 'schema'
              ? 'bg-zinc-800 text-white shadow-sm'
              : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
          }`}
        >
          <Layers className="h-3.5 w-3.5" />
          <span>Schema</span>
          {schema?.tables && (
            <span className="ml-1 rounded-full bg-zinc-700/60 px-1.5 py-0.2 text-[10px] text-zinc-300">
              {schema.tables.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('starters')}
          className={`flex flex-1 items-center justify-center space-x-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-all ${
            activeTab === 'starters'
              ? 'bg-zinc-800 text-white shadow-sm'
              : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
          }`}
        >
          <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
          <span>Starters</span>
        </button>

        <button
          onClick={() => setActiveTab('history')}
          className={`flex flex-1 items-center justify-center space-x-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-all ${
            activeTab === 'history'
              ? 'bg-zinc-800 text-white shadow-sm'
              : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
          }`}
        >
          <History className="h-3.5 w-3.5" />
          <span>History</span>
          {history.length > 0 && (
            <span className="ml-1 rounded-full bg-indigo-500/20 px-1.5 py-0.2 text-[10px] text-indigo-300 font-semibold">
              {history.length}
            </span>
          )}
        </button>
      </div>

      {/* TAB CONTENT: Schema Browser */}
      {activeTab === 'schema' && (
        <div className="flex flex-1 flex-col overflow-hidden">
          {/* Search Box */}
          <div className="p-3 border-b border-zinc-800/60">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-zinc-500" />
              <input
                type="text"
                placeholder="Search tables or columns..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-lg border border-zinc-800 bg-zinc-900/90 pl-8 pr-3 py-1.5 text-xs text-zinc-200 placeholder-zinc-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Table List Tree */}
          <div className="flex-1 overflow-y-auto p-2 space-y-1.5 scrollbar-thin scrollbar-thumb-zinc-800">
            {isLoadingSchema ? (
              <div className="space-y-2 p-2">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="h-10 rounded-lg bg-zinc-900/60 animate-pulse" />
                ))}
              </div>
            ) : filteredTables.length === 0 ? (
              <div className="p-6 text-center text-xs text-zinc-500">
                No matching tables or columns found.
              </div>
            ) : (
              filteredTables.map((table) => {
                const isExpanded = !!expandedTables[table.name];
                return (
                  <div
                    key={table.name}
                    className="rounded-lg border border-zinc-800/60 bg-zinc-900/40 overflow-hidden transition-colors hover:border-zinc-700/60"
                  >
                    {/* Table Header Row */}
                    <div
                      onClick={() => toggleTable(table.name)}
                      className="flex cursor-pointer items-center justify-between px-2.5 py-2 hover:bg-zinc-900/80 transition-colors"
                    >
                      <div className="flex items-center space-x-2 min-w-0">
                        {isExpanded ? (
                          <ChevronDown className="h-3.5 w-3.5 text-zinc-400 shrink-0" />
                        ) : (
                          <ChevronRight className="h-3.5 w-3.5 text-zinc-400 shrink-0" />
                        )}
                        <Table2 className="h-3.5 w-3.5 text-indigo-400 shrink-0" />
                        <span className="font-mono text-xs font-medium text-zinc-200 truncate">
                          {table.name}
                        </span>
                      </div>
                      <div className="flex items-center space-x-1.5 shrink-0">
                        <span className="rounded bg-zinc-800/80 px-1.5 py-0.5 text-[10px] font-mono text-zinc-400">
                          {table.row_count > 1000
                            ? `${(table.row_count / 1000).toFixed(0)}k`
                            : table.row_count}
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onOpenTableDetails(table);
                          }}
                          title="View table schema details"
                          className="text-zinc-500 hover:text-indigo-300"
                        >
                          <Info className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>

                    {/* Columns Accordion Sub-list */}
                    {isExpanded && (
                      <div className="border-t border-zinc-800/50 bg-zinc-950/60 px-2 py-1.5 space-y-1">
                        {table.columns.map((col) => (
                          <div
                            key={col.name}
                            className="flex items-center justify-between rounded px-2 py-1 text-[11px] hover:bg-zinc-900/60 transition-colors"
                          >
                            <div className="flex items-center space-x-1.5 min-w-0">
                              {col.is_pk && (
                                <Key className="h-3 w-3 text-amber-400 shrink-0" title="Primary Key" />
                              )}
                              {col.is_fk && (
                                <Link2 className="h-3 w-3 text-indigo-400 shrink-0" title="Foreign Key" />
                              )}
                              <span
                                className={`font-mono truncate ${
                                  col.is_pk
                                    ? 'text-amber-200 font-medium'
                                    : col.is_fk
                                    ? 'text-indigo-200'
                                    : 'text-zinc-300'
                                }`}
                              >
                                {col.name}
                              </span>
                            </div>
                            <span className="font-mono text-[10px] text-zinc-500 shrink-0">
                              {col.type}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* TAB CONTENT: Starter Prompts */}
      {activeTab === 'starters' && (
        <div className="flex-1 overflow-y-auto p-3 space-y-4 scrollbar-thin scrollbar-thumb-zinc-800">
          <div className="text-[11px] text-zinc-400 leading-relaxed">
            Select any enterprise query starter to immediately run analytical SQL against the 500,000+ transaction dataset:
          </div>
          {STARTER_PROMPTS.map((group) => {
            const Icon = group.icon;
            return (
              <div key={group.category} className="space-y-1.5">
                <div className="flex items-center space-x-1.5 text-xs font-semibold text-zinc-300">
                  <Icon className={`h-3.5 w-3.5 ${group.color}`} />
                  <span>{group.category}</span>
                </div>
                <div className="space-y-1">
                  {group.prompts.map((prompt) => (
                    <button
                      key={prompt}
                      onClick={() => onSelectPrompt(prompt)}
                      className="w-full rounded-lg border border-zinc-800/80 bg-zinc-900/50 p-2 text-left text-xs text-zinc-300 transition-all hover:border-indigo-500/50 hover:bg-zinc-850 hover:text-white group"
                    >
                      <span className="line-clamp-2">{prompt}</span>
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* TAB CONTENT: Query History */}
      {activeTab === 'history' && (
        <div className="flex-1 overflow-y-auto p-3 space-y-2 scrollbar-thin scrollbar-thumb-zinc-800">
          {history.length === 0 ? (
            <div className="p-8 text-center text-xs text-zinc-500">
              <Clock className="mx-auto mb-2 h-6 w-6 text-zinc-600" />
              No queries executed yet. Run a prompt to build your session history.
            </div>
          ) : (
            history.map((item) => (
              <div
                key={item.id}
                onClick={() => onSelectHistory(item)}
                className="cursor-pointer rounded-lg border border-zinc-800/80 bg-zinc-900/60 p-2.5 transition-all hover:border-indigo-500/60 hover:bg-zinc-900 group"
              >
                <p className="line-clamp-2 text-xs font-medium text-zinc-200 group-hover:text-indigo-200">
                  {item.question}
                </p>
                <div className="mt-2 flex items-center justify-between text-[10px] text-zinc-500">
                  <div className="flex items-center space-x-1.5">
                    <span className="font-mono text-zinc-400">{item.rowCount} rows</span>
                    <span>•</span>
                    <span className="flex items-center text-emerald-400 font-mono">
                      <Zap className="mr-0.5 h-2.5 w-2.5" />
                      {item.executionTimeMs.toFixed(0)}ms
                    </span>
                  </div>
                  <span>{item.timestamp}</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </aside>
  );
};

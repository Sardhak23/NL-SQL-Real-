import React, { useState, useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  ColumnDef,
  SortingState,
} from '@tanstack/react-table';
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Download,
  Search,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Database,
} from 'lucide-react';
import { formatCellContent } from '../../utils/formatters';
import { exportToCSV } from '../../utils/export';

interface DataTableProps {
  rows: Record<string, any>[];
  columns: string[];
  question?: string;
}

export const DataTable: React.FC<DataTableProps> = ({ rows, columns, question = 'nl_sql_query_result' }) => {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState('');
  const [pageSize, setPageSize] = useState(10);

  // Dynamic Column Definitions for TanStack Table
  const tableColumns = useMemo<ColumnDef<Record<string, any>>[]>(() => {
    return columns.map((col) => ({
      accessorKey: col,
      header: ({ column }) => {
        const isSorted = column.getIsSorted();
        return (
          <button
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="flex items-center space-x-1.5 font-mono text-xs font-semibold text-zinc-300 hover:text-white transition-colors"
          >
            <span>{col}</span>
            {isSorted === 'asc' ? (
              <ArrowUp className="h-3 w-3 text-indigo-400" />
            ) : isSorted === 'desc' ? (
              <ArrowDown className="h-3 w-3 text-indigo-400" />
            ) : (
              <ArrowUpDown className="h-3 w-3 text-zinc-600 opacity-60" />
            )}
          </button>
        );
      },
      cell: (info) => {
        const val = info.getValue();
        return (
          <span className="font-mono text-xs text-zinc-200">
            {formatCellContent(val, col)}
          </span>
        );
      },
    }));
  }, [columns]);

  const table = useReactTable({
    data: rows,
    columns: tableColumns,
    state: {
      sorting,
      globalFilter,
    },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: {
        pageSize: 10,
      },
    },
  });

  const handleExportCSV = () => {
    exportToCSV(question, rows, columns);
  };

  return (
    <div className="space-y-3 rounded-xl border border-zinc-800/80 bg-zinc-950/60 p-4 shadow-lg backdrop-blur-xl">
      {/* Controls Bar: Search & Export */}
      <div className="flex flex-col justify-between gap-2.5 sm:flex-row sm:items-center">
        {/* Global Search */}
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-zinc-500" />
          <input
            type="text"
            placeholder="Search within results..."
            value={globalFilter ?? ''}
            onChange={(e) => setGlobalFilter(e.target.value)}
            className="w-full rounded-lg border border-zinc-800 bg-zinc-900/90 pl-8 pr-3 py-1.5 text-xs text-zinc-200 placeholder-zinc-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        {/* Metadata and Actions */}
        <div className="flex items-center space-x-2">
          {/* Row Count Badge */}
          <div className="flex items-center space-x-1.5 rounded-lg border border-zinc-800 bg-zinc-900/80 px-2.5 py-1 text-xs text-zinc-400">
            <Database className="h-3 w-3 text-indigo-400" />
            <span className="font-mono text-zinc-200 font-medium">
              {table.getFilteredRowModel().rows.length}
            </span>
            <span>of</span>
            <span className="font-mono text-zinc-200">{rows.length}</span>
            <span>rows</span>
          </div>

          {/* Export CSV Button */}
          <button
            onClick={handleExportCSV}
            disabled={rows.length === 0}
            className="flex items-center space-x-1.5 rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-1 text-xs font-medium text-zinc-300 transition-colors hover:border-indigo-500/60 hover:bg-zinc-850 hover:text-white disabled:opacity-50"
          >
            <Download className="h-3.5 w-3.5 text-indigo-400" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Table Render Container */}
      <div className="overflow-x-auto rounded-lg border border-zinc-800/80 bg-zinc-900/40">
        <table className="w-full text-left border-collapse">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="border-b border-zinc-800 bg-zinc-900/90">
                {headerGroup.headers.map((header) => (
                  <th key={header.id} className="px-3.5 py-2.5 text-left">
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-zinc-800/60">
            {table.getRowModel().rows.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-8 text-center text-xs text-zinc-500"
                >
                  No matching records found.
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  className="hover:bg-zinc-800/40 transition-colors"
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-3.5 py-2">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="flex flex-col items-center justify-between gap-2 text-xs text-zinc-400 sm:flex-row pt-1">
        {/* Page Size Selector */}
        <div className="flex items-center space-x-2">
          <span>Show</span>
          <select
            value={pageSize}
            onChange={(e) => {
              const size = Number(e.target.value);
              setPageSize(size);
              table.setPageSize(size);
            }}
            className="rounded border border-zinc-800 bg-zinc-900 px-2 py-1 text-xs text-zinc-300 focus:border-indigo-500 focus:outline-none"
          >
            {[10, 25, 50, 100].map((s) => (
              <option key={s} value={s}>
                {s} rows
              </option>
            ))}
          </select>
          <span>per page</span>
        </div>

        {/* Page Navigation Buttons */}
        <div className="flex items-center space-x-1.5">
          <span className="font-mono text-zinc-300">
            Page {table.getState().pagination.pageIndex + 1} of{' '}
            {Math.max(1, table.getPageCount())}
          </span>

          <div className="flex items-center space-x-1">
            <button
              onClick={() => table.setPageIndex(0)}
              disabled={!table.getCanPreviousPage()}
              className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white disabled:opacity-40"
            >
              <ChevronsLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white disabled:opacity-40"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white disabled:opacity-40"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
            <button
              onClick={() => table.setPageIndex(table.getPageCount() - 1)}
              disabled={!table.getCanNextPage()}
              className="rounded p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white disabled:opacity-40"
            >
              <ChevronsRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

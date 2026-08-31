import React from 'react';
import { X, Table2, Key, Link2, Database, Layers } from 'lucide-react';
import { TableMetadata } from '../../types';

interface TableDetailsModalProps {
  table: TableMetadata | null;
  onClose: () => void;
}

export const TableDetailsModal: React.FC<TableDetailsModalProps> = ({ table, onClose }) => {
  if (!table) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
      <div className="w-full max-w-2xl rounded-2xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl space-y-4">
        {/* Modal Header */}
        <div className="flex items-start justify-between border-b border-zinc-800 pb-3">
          <div className="flex items-center space-x-3">
            <div className="rounded-xl bg-indigo-500/10 p-2 text-indigo-400">
              <Table2 className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="font-mono text-base font-bold text-white">
                  {table.name}
                </h3>
                <span className="rounded bg-zinc-800 px-2 py-0.5 font-mono text-xs text-zinc-300">
                  {table.row_count.toLocaleString()} rows
                </span>
              </div>
              <p className="text-xs text-zinc-400 mt-0.5">
                {table.description || 'Database entity table'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Columns Table */}
        <div className="max-h-80 overflow-y-auto rounded-lg border border-zinc-800/80 bg-zinc-900/40">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-zinc-800 bg-zinc-900/90 font-semibold text-zinc-300">
                <th className="px-4 py-2.5">Column Name</th>
                <th className="px-4 py-2.5">Data Type</th>
                <th className="px-4 py-2.5">Key Attributes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 font-mono">
              {table.columns.map((col) => (
                <tr key={col.name} className="hover:bg-zinc-800/30">
                  <td className="px-4 py-2 text-zinc-200 font-medium">{col.name}</td>
                  <td className="px-4 py-2 text-zinc-400">{col.type}</td>
                  <td className="px-4 py-2">
                    <div className="flex items-center space-x-2">
                      {col.is_pk && (
                        <span className="flex items-center space-x-1 rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] text-amber-400">
                          <Key className="h-3 w-3" />
                          <span>PRIMARY KEY</span>
                        </span>
                      )}
                      {col.is_fk && (
                        <span className="flex items-center space-x-1 rounded bg-indigo-500/10 px-1.5 py-0.5 text-[10px] text-indigo-400">
                          <Link2 className="h-3 w-3" />
                          <span>FOREIGN KEY</span>
                        </span>
                      )}
                      {!col.is_pk && !col.is_fk && (
                        <span className="text-[10px] text-zinc-500">Standard</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Foreign Keys Reference Section */}
        {table.foreign_keys && table.foreign_keys.length > 0 && (
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3 space-y-1.5">
            <div className="flex items-center space-x-1.5 text-xs font-semibold text-zinc-300">
              <Link2 className="h-3.5 w-3.5 text-indigo-400" />
              <span>Relational Foreign Keys:</span>
            </div>
            <ul className="space-y-1 font-mono text-[11px] text-zinc-400">
              {table.foreign_keys.map((fk, idx) => (
                <li key={idx} className="flex items-center space-x-1.5">
                  <span className="text-indigo-400">{fk.column}</span>
                  <span className="text-zinc-600">➔</span>
                  <span className="text-zinc-200">{fk.referenced_table}.{fk.referenced_column}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Modal Footer */}
        <div className="flex justify-end pt-2">
          <button
            onClick={onClose}
            className="rounded-lg bg-zinc-800 px-4 py-1.5 text-xs font-medium text-zinc-200 hover:bg-zinc-700 hover:text-white"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

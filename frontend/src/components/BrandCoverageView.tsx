import React from 'react';
import { Layers, ShieldCheck, AlertTriangle, Users } from 'lucide-react';
import { RosterViewData, PodData } from '../types';

interface BrandCoverageViewProps {
  data: RosterViewData;
  pods: PodData[];
  selectedPod: number | null;
  onSelectPod: (podId: number | null) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
}

export const BrandCoverageView: React.FC<BrandCoverageViewProps> = ({
  data,
  pods,
  selectedPod,
  onSelectPod,
  searchQuery,
  onSearchChange,
}) => {
  const getWeekday = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { weekday: 'short' });
  };

  const isWeekend = (dateStr: string) => {
    const d = new Date(dateStr);
    const day = d.getDay();
    return day === 0 || day === 6;
  };

  return (
    <div className="space-y-4">
      {/* Filters Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3 flex-1">
          <input
            type="text"
            placeholder="Search brand or process..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="text-xs py-1.5 px-3 rounded-lg border border-slate-300 w-64 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />

          <select
            value={selectedPod ?? ''}
            onChange={(e) => onSelectPod(e.target.value ? Number(e.target.value) : null)}
            className="text-xs py-1.5 px-3 rounded-lg border border-slate-300 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="">All Pods</option>
            {pods.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        {/* Legend */}
        <div className="flex items-center space-x-3 text-xs font-medium text-slate-600">
          <div className="flex items-center space-x-1">
            <span className="w-3 h-3 rounded bg-emerald-100 border border-emerald-300"></span>
            <span>Fulfilled (≥ Min Staff)</span>
          </div>
          <div className="flex items-center space-x-1">
            <span className="w-3 h-3 rounded bg-red-100 border border-red-300"></span>
            <span>Headcount Deficit (GAP)</span>
          </div>
          <div className="flex items-center space-x-1">
            <span className="w-3 h-3 rounded bg-slate-100 border border-slate-300"></span>
            <span>Closed / Off</span>
          </div>
        </div>
      </div>

      {/* Coverage Matrix Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto max-h-[720px] relative">
          <table className="border-collapse text-left text-xs min-w-full">
            <thead className="bg-slate-50 text-slate-700 sticky top-0 z-20 shadow-xs border-b border-slate-200">
              <tr>
                <th className="sticky left-0 z-30 bg-slate-100 py-3 px-3.5 font-bold min-w-[200px] border-r border-slate-200">
                  Brand Name
                </th>
                <th className="sticky left-[200px] z-30 bg-slate-100 py-3 px-2.5 font-semibold min-w-[150px] border-r border-slate-200">
                  Process
                </th>

                {data.days.map((d) => {
                  const dayNum = d.split('-')[2];
                  const weekday = getWeekday(d);
                  const weekend = isWeekend(d);

                  return (
                    <th
                      key={d}
                      className={`py-2 px-2 text-center min-w-[65px] border-r border-slate-200 ${
                        weekend ? 'bg-slate-100/70' : ''
                      }`}
                    >
                      <div className="text-[10px] text-slate-400 font-semibold">{weekday}</div>
                      <div className="text-sm font-extrabold text-slate-800">{dayNum}</div>
                    </th>
                  );
                })}
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {data.coverage_rows.length === 0 ? (
                <tr>
                  <td colSpan={data.days.length + 2} className="py-12 text-center text-slate-400">
                    No brand coverage requirements match your filters.
                  </td>
                </tr>
              ) : (
                data.coverage_rows.map((row) => (
                  <tr key={`${row.brand_id}-${row.process_id}`} className="hover:bg-slate-50/70 transition">
                    <td className="sticky left-0 z-10 bg-white py-2.5 px-3.5 border-r border-slate-200 font-bold text-slate-900 shadow-sm">
                      {row.brand_name}
                    </td>
                    <td className="sticky left-[200px] z-10 bg-white py-2.5 px-2.5 border-r border-slate-200 text-slate-600 font-medium">
                      {row.process_name} <span className="text-[10px] text-slate-400 font-mono">({row.process_code})</span>
                    </td>

                    {row.cells.map((cell) => {
                      let cellClass = 'bg-white text-slate-400';
                      let content = '—';

                      if (cell.state === 'closed') {
                        cellClass = 'bg-slate-50 text-slate-300';
                        content = 'Closed';
                      } else if (cell.state === 'covered') {
                        cellClass = 'bg-emerald-50 text-emerald-800 font-bold border-emerald-100';
                        content = `${cell.assigned}/${cell.required}`;
                      } else if (cell.state === 'gap') {
                        cellClass = 'bg-red-50 text-red-900 font-extrabold border-red-200 animate-pulse';
                        content = `${cell.assigned}/${cell.required} GAP`;
                      }

                      return (
                        <td
                          key={cell.date}
                          className={`py-2 px-1 text-center border-r border-slate-200 text-[11px] ${cellClass}`}
                          title={
                            cell.employees.length > 0
                              ? `Assigned: ${cell.employees.join(', ')}`
                              : cell.state === 'gap'
                              ? 'Deficit: Needs active authorised personnel'
                              : 'Closed'
                          }
                        >
                          {content}
                        </td>
                      );
                    })}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

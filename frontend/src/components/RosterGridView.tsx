import React, { useState } from 'react';
import {
  Search,
  Filter,
  Info,
  Calendar,
  AlertCircle,
  Sparkles,
} from 'lucide-react';
import { RosterViewData, RosterRow, CellOut, PodData, BrandData } from '../types';

interface RosterGridViewProps {
  data: RosterViewData;
  pods: PodData[];
  brands: BrandData[];
  selectedPod: number | null;
  onSelectPod: (podId: number | null) => void;
  selectedBrand: number | null;
  onSelectBrand: (brandId: number | null) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onCellClick: (employeeId: number, employeeName: string, date: string, cell: CellOut) => void;
}

export const RosterGridView: React.FC<RosterGridViewProps> = ({
  data,
  pods,
  brands,
  selectedPod,
  onSelectPod,
  selectedBrand,
  onSelectBrand,
  searchQuery,
  onSearchChange,
  onCellClick,
}) => {
  // Helper to format weekday from date string YYYY-MM-DD
  const getWeekday = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { weekday: 'short' });
  };

  const isWeekend = (dateStr: string) => {
    const d = new Date(dateStr);
    const day = d.getDay();
    return day === 0 || day === 6; // Sunday or Saturday
  };

  return (
    <div className="space-y-4">
      {/* Filter and Control Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3 flex-1">
          {/* Search Input */}
          <div className="relative min-w-[200px] max-w-xs flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Filter by name or employee code..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
            />
          </div>

          {/* Pod Filter */}
          <select
            value={selectedPod ?? ''}
            onChange={(e) => onSelectPod(e.target.value ? Number(e.target.value) : null)}
            className="text-xs py-1.5 px-3 rounded-lg border border-slate-300 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="">All Operational Pods</option>
            {pods.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.code})
              </option>
            ))}
          </select>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-600 font-medium">
          <div className="flex items-center space-x-1">
            <span className="w-3 h-3 rounded bg-emerald-100 border border-emerald-300"></span>
            <span>Working</span>
          </div>
          <div className="flex items-center space-x-1">
            <span className="w-3 h-3 rounded bg-slate-100 border border-slate-300"></span>
            <span>Weekly Off</span>
          </div>
          <div className="flex items-center space-x-1">
            <span className="w-3 h-3 rounded bg-amber-100 border border-amber-300"></span>
            <span>Leave</span>
          </div>
          <div className="flex items-center space-x-1">
            <span className="w-3 h-3 rounded bg-purple-100 border border-purple-300"></span>
            <span>Public Holiday</span>
          </div>
          <div className="flex items-center space-x-1">
            <span className="w-3 h-3 rounded bg-red-100 border border-red-300"></span>
            <span>Unavailable</span>
          </div>
        </div>
      </div>

      {/* Main Interactive Matrix */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto max-h-[720px] relative">
          <table className="border-collapse text-left text-xs min-w-full">
            {/* Table Header */}
            <thead className="bg-slate-50 text-slate-700 sticky top-0 z-20 shadow-xs border-b border-slate-200">
              <tr>
                <th className="sticky left-0 z-30 bg-slate-100 py-3 px-3.5 font-bold min-w-[220px] border-r border-slate-200">
                  Employee & Pod
                </th>
                <th className="sticky left-[220px] z-30 bg-slate-100 py-3 px-2.5 font-semibold min-w-[130px] border-r border-slate-200">
                  Role / Cap
                </th>

                {data.days.map((d) => {
                  const dayNum = d.split('-')[2];
                  const weekday = getWeekday(d);
                  const weekend = isWeekend(d);
                  const holiday = data.holidays.find((h) => h.date === d);

                  return (
                    <th
                      key={d}
                      className={`py-2 px-2 text-center min-w-[70px] border-r border-slate-200 ${
                        weekend ? 'bg-slate-100/70 font-bold' : ''
                      } ${holiday ? 'bg-purple-50 text-purple-900' : ''}`}
                    >
                      <div className="text-[10px] text-slate-500 uppercase font-semibold">{weekday}</div>
                      <div className="text-sm font-extrabold text-slate-800">{dayNum}</div>
                      {holiday && (
                        <div className="text-[9px] text-purple-700 truncate max-w-[65px]" title={holiday.name}>
                          {holiday.name}
                        </div>
                      )}
                    </th>
                  );
                })}
              </tr>
            </thead>

            {/* Table Body */}
            <tbody className="divide-y divide-slate-100">
              {data.rows.length === 0 ? (
                <tr>
                  <td colSpan={data.days.length + 2} className="py-12 text-center text-slate-400">
                    No employees matching the selected filters.
                  </td>
                </tr>
              ) : (
                data.rows.map((row) => (
                  <tr key={row.employee_id} className="hover:bg-slate-50/70 transition">
                    {/* Sticky Employee Column */}
                    <td className="sticky left-0 z-10 bg-white py-2.5 px-3.5 border-r border-slate-200 shadow-sm">
                      <div className="font-bold text-slate-900 flex items-center space-x-1.5">
                        <span>{row.full_name}</span>
                        {row.is_pod_lead && (
                          <span className="px-1.5 py-0.2 rounded text-[10px] bg-indigo-100 text-indigo-800 font-semibold">
                            Lead
                          </span>
                        )}
                      </div>
                      <div className="flex items-center space-x-2 text-[11px] text-slate-500 mt-0.5">
                        <span className="font-mono text-slate-400">{row.employee_code}</span>
                        <span>•</span>
                        <span className="text-brand-700 font-medium">{row.pod_name}</span>
                      </div>
                    </td>

                    {/* Sticky Role / Capacity Column */}
                    <td className="sticky left-[220px] z-10 bg-white py-2.5 px-2.5 border-r border-slate-200 text-[11px] text-slate-600">
                      <div className="truncate max-w-[120px]" title={row.designation}>
                        {row.designation}
                      </div>
                    </td>

                    {/* Daily Shift Cells */}
                    {row.cells.map((cell) => {
                      let cellClass = 'bg-white text-slate-400';
                      let label = '';
                      let sublabel = '';

                      switch (cell.status) {
                        case 'working':
                          cellClass = 'bg-emerald-50 text-emerald-900 border-emerald-200 hover:bg-emerald-100';
                          label = cell.brands[0] || 'Work';
                          if (cell.brands.length > 1) sublabel = `+${cell.brands.length - 1} more`;
                          break;
                        case 'weekly_off':
                          cellClass = 'bg-slate-100 text-slate-500 hover:bg-slate-200';
                          label = 'OFF';
                          break;
                        case 'approved_leave':
                          cellClass = 'bg-amber-50 text-amber-900 border-amber-200 hover:bg-amber-100';
                          label = 'LEAVE';
                          break;
                        case 'comp_off':
                          cellClass = 'bg-indigo-50 text-indigo-900 border-indigo-200 hover:bg-indigo-100';
                          label = 'COMP-OFF';
                          break;
                        case 'public_holiday':
                          cellClass = 'bg-purple-50 text-purple-900 border-purple-200 hover:bg-purple-100';
                          label = 'HOLIDAY';
                          break;
                        case 'unavailable':
                          cellClass = 'bg-red-50 text-red-900 border-red-200 hover:bg-red-100 font-bold';
                          label = 'UNAVAIL';
                          break;
                        case 'available':
                          cellClass = 'bg-white text-slate-400 hover:bg-slate-50';
                          label = '—';
                          break;
                        case 'calendar_off':
                          cellClass = 'bg-slate-50 text-slate-400';
                          label = 'Closed';
                          break;
                      }

                      return (
                        <td
                          key={cell.date}
                          onClick={() => onCellClick(row.employee_id, row.full_name, cell.date, cell)}
                          className={`py-2 px-1 text-center border-r border-slate-200 cursor-pointer select-none transition relative ${cellClass}`}
                          title={`Click to edit or simulate override for ${row.full_name} on ${cell.date}`}
                        >
                          {/* Gap Indicator Dot */}
                          {cell.has_gap && (
                            <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                          )}
                          <div className="font-semibold text-[11px] truncate">{label}</div>
                          {sublabel && <div className="text-[9px] text-emerald-700 font-medium">{sublabel}</div>}
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

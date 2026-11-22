import React from 'react';
import {
  Users,
  ShieldCheck,
  Building2,
  CalendarCheck2,
  AlertTriangle,
  ArrowUpRight,
  TrendingUp,
  Clock,
  Layers,
  CheckCircle,
} from 'lucide-react';
import { DashboardData } from '../types';

interface DashboardViewProps {
  data: DashboardData;
  onNavigateToConflicts: () => void;
  onNavigateToRoster: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  data,
  onNavigateToConflicts,
  onNavigateToRoster,
}) => {
  return (
    <div className="space-y-6">
      {/* Top Banner Notice */}
      {data.unresolved_conflicts > 0 && (
        <div className="bg-gradient-to-r from-red-500/10 via-amber-500/10 to-transparent p-4 rounded-xl border border-red-200 flex items-center justify-between shadow-xs">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-red-100 rounded-lg text-red-700">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-red-900">
                Action Required: {data.unresolved_conflicts} Unresolved Scheduling Conflict(s)
              </h4>
              <p className="text-xs text-red-700">
                Operating demand exceeds assigned active staff. Open the resolution drawer to review automated assignment suggestions.
              </p>
            </div>
          </div>
          <button
            onClick={onNavigateToConflicts}
            className="px-3.5 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-semibold shadow-xs transition flex items-center space-x-1"
          >
            <span>Review & Resolve</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Coverage Card */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Operational Coverage</span>
            <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-slate-900">{data.coverage_percent}%</span>
            <span className="text-xs font-medium text-emerald-600">target: 100%</span>
          </div>
          <div className="mt-3 w-full bg-slate-100 h-2 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                data.coverage_percent >= 95 ? 'bg-emerald-500' : data.coverage_percent >= 85 ? 'bg-amber-500' : 'bg-red-500'
              }`}
              style={{ width: `${Math.min(100, data.coverage_percent)}%` }}
            />
          </div>
        </div>

        {/* Active Staff Card */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Employees</span>
            <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-slate-900">{data.active_employees}</span>
            <span className="text-xs font-medium text-slate-500">/ {data.total_employees} Total</span>
          </div>
          <p className="mt-3 text-xs text-slate-500">
            {data.total_employees - data.active_employees} inactive or on notice
          </p>
        </div>

        {/* Pods & Brands */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pods & Clients</span>
            <div className="p-2 rounded-lg bg-indigo-50 text-indigo-600">
              <Building2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-slate-900">{data.total_brands}</span>
            <span className="text-xs font-medium text-indigo-600">Brands across {data.total_pods} Pods</span>
          </div>
          <p className="mt-3 text-xs text-slate-500">{data.total_processes} Operational Processes</p>
        </div>

        {/* Staff on Leave */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Approved Absences</span>
            <div className="p-2 rounded-lg bg-amber-50 text-amber-600">
              <CalendarCheck2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-slate-900">{data.employees_on_leave}</span>
            <span className="text-xs font-medium text-amber-600">employees this month</span>
          </div>
          <p className="mt-3 text-xs text-slate-500">Includes planned & sick leaves</p>
        </div>
      </div>

      {/* Middle Row: Brand Coverage Health & Status Mix */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Brand Coverage Health Breakdown (2 cols) */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Brand Coverage Compliance</h3>
              <p className="text-xs text-slate-500">Live operational fulfillment rate per brand</p>
            </div>
            <button
              onClick={onNavigateToRoster}
              className="text-xs font-semibold text-brand-600 hover:text-brand-800 flex items-center space-x-1"
            >
              <span>View Roster Grid</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-80 overflow-y-auto pr-1">
            {data.brand_coverage.map((b) => (
              <div
                key={b.id}
                className="p-3 rounded-lg border border-slate-100 hover:border-slate-300 bg-slate-50/50 transition flex items-center justify-between"
              >
                <div>
                  <h5 className="text-xs font-semibold text-slate-800 truncate max-w-[160px]">{b.name}</h5>
                  <p className="text-[11px] text-slate-500">
                    {b.met} of {b.total} slots fulfilled
                  </p>
                </div>
                <div className="text-right">
                  <span
                    className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                      b.coverage === 100
                        ? 'bg-emerald-100 text-emerald-800'
                        : b.coverage >= 80
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {b.coverage}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Shift Status Mix Distribution */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
          <div className="pb-3 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900">Shift Status Breakdown</h3>
            <p className="text-xs text-slate-500">Distribution across 30 days of schedule</p>
          </div>

          <div className="my-4 space-y-2.5">
            {data.status_mix.map((item) => {
              const total = data.status_mix.reduce((acc, x) => acc + x.value, 0) || 1;
              const percent = Math.round((item.value / total) * 100);

              let badgeColor = 'bg-slate-200 text-slate-700';
              if (item.key === 'working') badgeColor = 'bg-emerald-500 text-white';
              if (item.key === 'weekly_off') badgeColor = 'bg-slate-400 text-white';
              if (item.key === 'approved_leave') badgeColor = 'bg-amber-400 text-white';
              if (item.key === 'public_holiday') badgeColor = 'bg-purple-500 text-white';
              if (item.key === 'unavailable') badgeColor = 'bg-red-500 text-white';

              return (
                <div key={item.key} className="space-y-1">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-slate-600">{item.name}</span>
                    <span className="text-slate-900 font-bold">{item.value} ({percent}%)</span>
                  </div>
                  <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${
                        item.key === 'working'
                          ? 'bg-emerald-500'
                          : item.key === 'approved_leave'
                          ? 'bg-amber-500'
                          : item.key === 'public_holiday'
                          ? 'bg-purple-500'
                          : item.key === 'unavailable'
                          ? 'bg-red-500'
                          : 'bg-slate-400'
                      }`}
                      style={{ width: `${percent}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs text-slate-600">
            <span className="font-semibold text-slate-800">Deterministic Engine:</span> Workload cap guarantees ≤ 1 brand/day (or authorized max), weekly offs aligned with brand operations.
          </div>
        </div>
      </div>

      {/* Bottom Row: Employees on Leave & Recent Audit Logs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Approved Absences Table */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Approved Leaves & Absences</h3>
              <p className="text-xs text-slate-500">Personnel unavailable for shift allocation</p>
            </div>
            <span className="text-xs font-semibold px-2 py-0.5 bg-amber-50 text-amber-700 border border-amber-200 rounded-md">
              {data.on_leave.length} Scheduled
            </span>
          </div>

          <div className="mt-3 overflow-x-auto">
            {data.on_leave.length === 0 ? (
              <p className="text-xs text-slate-400 py-4 text-center">No approved leaves recorded for this month.</p>
            ) : (
              <table className="min-w-full divide-y divide-slate-100 text-left text-xs">
                <thead>
                  <tr className="text-slate-400 font-medium">
                    <th className="py-2">Employee</th>
                    <th className="py-2">Pod</th>
                    <th className="py-2">Duration</th>
                    <th className="py-2">Type</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {data.on_leave.map((l) => (
                    <tr key={l.id} className="hover:bg-slate-50/50">
                      <td className="py-2.5 font-semibold text-slate-800">
                        {l.employee_name} <span className="text-[10px] text-slate-400">({l.employee_code})</span>
                      </td>
                      <td className="py-2.5 text-slate-600">{l.pod_name}</td>
                      <td className="py-2.5 text-slate-600">
                        {l.start_date === l.end_date ? l.start_date : `${l.start_date} → ${l.end_date}`}
                      </td>
                      <td className="py-2.5">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-800 uppercase">
                          {l.leave_type}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Recent Audit Logs Stream */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900">System & Manager Audit Log</h3>
              <p className="text-xs text-slate-500">Immutable ledger of overrides, solves and updates</p>
            </div>
            <Clock className="w-4 h-4 text-slate-400" />
          </div>

          <div className="mt-3 space-y-2.5 max-h-60 overflow-y-auto pr-1">
            {data.recent_changes.map((log) => (
              <div key={log.id} className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs">
                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <span className="font-semibold uppercase text-brand-700">{log.action.replace('_', ' ')}</span>
                  <span>{new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
                <p className="mt-1 text-slate-700 font-medium">{log.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

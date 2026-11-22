import React, { useState } from 'react';
import { Calendar, Check, X, AlertCircle, Clock, CheckCircle2, UserCheck } from 'lucide-react';
import { LeaveData } from '../types';

interface LeavesViewProps {
  leaves: LeaveData[];
  onUpdateStatus: (leaveId: number, status: 'approved' | 'rejected') => Promise<void>;
  isUpdating: boolean;
}

export const LeavesView: React.FC<LeavesViewProps> = ({
  leaves,
  onUpdateStatus,
  isUpdating,
}) => {
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  const handleAction = async (id: number, status: 'approved' | 'rejected') => {
    setUpdatingId(id);
    try {
      await onUpdateStatus(id, status);
    } finally {
      setUpdatingId(null);
    }
  };

  const pendingLeaves = leaves.filter((l) => l.status === 'pending');
  const pastLeaves = leaves.filter((l) => l.status !== 'pending');

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
            <Calendar className="w-5 h-5 text-brand-600" />
            <span>Personnel Absence & Leave Approvals</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Pending leave requests block scheduling only once approved. Approving immediately triggers automated schedule re-solve.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs font-semibold">
          <span className="px-3 py-1.5 rounded-lg bg-amber-50 text-amber-800 border border-amber-200">
            {pendingLeaves.length} Pending Actions
          </span>
          <span className="px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200">
            {leaves.filter((l) => l.status === 'approved').length} Active Approved
          </span>
        </div>
      </div>

      {/* Pending Approvals Section */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5">
        <h3 className="text-sm font-bold text-slate-900 pb-3 border-b border-slate-100 flex items-center justify-between">
          <span>Pending Manager Review</span>
          <span className="text-xs font-normal text-slate-400">Click to approve or deny request</span>
        </h3>

        {pendingLeaves.length === 0 ? (
          <div className="py-8 text-center text-slate-400 text-xs">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
            No pending leave requests awaiting approval.
          </div>
        ) : (
          <div className="divide-y divide-slate-100 mt-2">
            {pendingLeaves.map((l) => (
              <div key={l.id} className="py-3.5 flex flex-wrap items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-bold text-slate-900">{l.employee_name}</span>
                    <span className="font-mono text-xs text-slate-400 font-semibold">{l.employee_code}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-100 text-amber-800">
                      {l.leave_type}
                    </span>
                  </div>
                  <div className="text-xs text-slate-600 flex items-center space-x-2">
                    <span>
                      📅 {l.start_date === l.end_date ? l.start_date : `${l.start_date} to ${l.end_date}`}
                    </span>
                    {l.reason && <span className="text-slate-400">• "{l.reason}"</span>}
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleAction(l.id, 'rejected')}
                    disabled={isUpdating}
                    className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-300 hover:bg-red-50 hover:text-red-700 hover:border-red-300 transition text-slate-700 flex items-center space-x-1"
                  >
                    <X className="w-3.5 h-3.5" />
                    <span>Reject</span>
                  </button>
                  <button
                    onClick={() => handleAction(l.id, 'approved')}
                    disabled={isUpdating}
                    className="px-3.5 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white transition shadow-xs flex items-center space-x-1"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>{updatingId === l.id ? 'Updating...' : 'Approve & Re-Solve'}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* History / Decisions Section */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5">
        <h3 className="text-sm font-bold text-slate-900 pb-3 border-b border-slate-100">
          Decided Leaves History
        </h3>

        <div className="overflow-x-auto mt-2">
          <table className="min-w-full divide-y divide-slate-100 text-left text-xs">
            <thead>
              <tr className="text-slate-400 font-medium">
                <th className="py-2.5">Employee</th>
                <th className="py-2.5">Date Range</th>
                <th className="py-2.5">Type</th>
                <th className="py-2.5">Reason</th>
                <th className="py-2.5">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {pastLeaves.map((l) => (
                <tr key={l.id} className="hover:bg-slate-50/50">
                  <td className="py-2.5 font-bold text-slate-800">
                    {l.employee_name} <span className="font-mono text-slate-400 font-normal">({l.employee_code})</span>
                  </td>
                  <td className="py-2.5 text-slate-600">
                    {l.start_date === l.end_date ? l.start_date : `${l.start_date} → ${l.end_date}`}
                  </td>
                  <td className="py-2.5 uppercase font-semibold text-[10px] text-slate-600">
                    {l.leave_type}
                  </td>
                  <td className="py-2.5 text-slate-500 max-w-xs truncate" title={l.reason}>
                    {l.reason || '—'}
                  </td>
                  <td className="py-2.5">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        l.status === 'approved'
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {l.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

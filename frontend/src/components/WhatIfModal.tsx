import React, { useState } from 'react';
import { X, Sparkles, AlertCircle, CheckCircle2, ShieldCheck, ArrowRight } from 'lucide-react';
import { CellOut, EmployeeData, BrandData, PreviewData, DayEditIn } from '../types';

interface WhatIfModalProps {
  isOpen: boolean;
  onClose: () => void;
  employeeId: number;
  employeeName: string;
  targetDate: string;
  initialCell: CellOut | null;
  employees: EmployeeData[];
  brands: BrandData[];
  onApplyOverride: (payload: DayEditIn) => Promise<void>;
  onPreview: (payload: DayEditIn) => Promise<PreviewData>;
}

export const WhatIfModal: React.FC<WhatIfModalProps> = ({
  isOpen,
  onClose,
  employeeId,
  employeeName,
  targetDate,
  initialCell,
  employees,
  brands,
  onApplyOverride,
  onPreview,
}) => {
  if (!isOpen) return null;

  const currentEmp = employees.find((e) => e.id === employeeId);

  const [status, setStatus] = useState<DayEditIn['status']>(
    (initialCell?.status as DayEditIn['status']) || 'working'
  );
  const [selectedBrandIds, setSelectedBrandIds] = useState<number[]>(
    initialCell?.brand_ids || []
  );
  const [note, setNote] = useState<string>('');
  const [authorise, setAuthorise] = useState<boolean>(true);

  const [previewResult, setPreviewResult] = useState<PreviewData | null>(null);
  const [isPreviewing, setIsPreviewing] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string>('');

  const handleBrandToggle = (brandId: number) => {
    if (selectedBrandIds.includes(brandId)) {
      setSelectedBrandIds(selectedBrandIds.filter((id) => id !== brandId));
    } else {
      setSelectedBrandIds([...selectedBrandIds, brandId]);
    }
  };

  const handleRunWhatIf = async () => {
    setIsPreviewing(true);
    setErrorMsg('');
    try {
      const payload: DayEditIn = {
        employee_id: employeeId,
        date: targetDate,
        status,
        brand_ids: status === 'working' ? selectedBrandIds : [],
        note,
        authorise,
      };
      const res = await onPreview(payload);
      setPreviewResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Simulation failed');
    } finally {
      setIsPreviewing(false);
    }
  };

  const handleCommit = async () => {
    setIsSaving(true);
    setErrorMsg('');
    try {
      const payload: DayEditIn = {
        employee_id: employeeId,
        date: targetDate,
        status,
        brand_ids: status === 'working' ? selectedBrandIds : [],
        note,
        authorise,
      };
      await onApplyOverride(payload);
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to save override');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-xl w-full border border-slate-200 shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900">What-If Manager Override Simulation</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Simulate shift modifications and evaluate constraint impact before persisting
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
          {errorMsg && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Context Card */}
          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
            <div>
              <span className="font-bold text-slate-800 text-sm">{employeeName}</span>
              <p className="text-slate-500 font-mono text-[11px] mt-0.5">
                {currentEmp?.employee_code} • {currentEmp?.pod_name} • Workload Cap: {currentEmp?.max_daily_workload} brand(s)
              </p>
            </div>
            <div className="text-right">
              <span className="font-semibold text-brand-700 bg-brand-50 px-2.5 py-1 rounded-md border border-brand-200">
                {targetDate}
              </span>
            </div>
          </div>

          {/* Target Status Selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-700">Target Shift Status</label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { key: 'working', label: 'Working' },
                { key: 'weekly_off', label: 'Weekly Off' },
                { key: 'approved_leave', label: 'Leave' },
                { key: 'comp_off', label: 'Comp-Off' },
                { key: 'unavailable', label: 'Unavailable' },
                { key: 'available', label: 'Available' },
              ].map((s) => (
                <button
                  key={s.key}
                  type="button"
                  onClick={() => setStatus(s.key as DayEditIn['status'])}
                  className={`py-2 px-3 rounded-lg text-xs font-semibold border transition ${
                    status === s.key
                      ? 'bg-brand-600 text-white border-brand-600 shadow-xs'
                      : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* Brand Assignment Selection (Only when status is working) */}
          {status === 'working' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-slate-700">Assign Brand(s) for this Day</label>
                <span className="text-[11px] text-slate-400">
                  Selected: {selectedBrandIds.length} / {currentEmp?.max_daily_workload || 1}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto p-1 border border-slate-200 rounded-lg">
                {brands.map((b) => {
                  const isSelected = selectedBrandIds.includes(b.id);
                  return (
                    <button
                      key={b.id}
                      type="button"
                      onClick={() => handleBrandToggle(b.id)}
                      className={`p-2 rounded-md text-left text-xs border transition ${
                        isSelected
                          ? 'bg-emerald-50 border-emerald-300 text-emerald-900 font-bold'
                          : 'bg-white border-slate-100 text-slate-600 hover:bg-slate-50'
                      }`}
                    >
                      <div className="truncate">{b.name}</div>
                      <div className="text-[10px] text-slate-400">{b.pod_name}</div>
                    </button>
                  );
                })}
              </div>

              <div className="flex items-center space-x-2 pt-1">
                <input
                  type="checkbox"
                  id="authorise-cb"
                  checked={authorise}
                  onChange={(e) => setAuthorise(e.target.checked)}
                  className="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                />
                <label htmlFor="authorise-cb" className="text-xs text-slate-600">
                  Grant process authorisation if colleague is not yet certified for these brands
                </label>
              </div>
            </div>
          )}

          {/* Note Input */}
          <div className="space-y-1">
            <label className="text-xs font-bold text-slate-700">Audit / Manager Note</label>
            <input
              type="text"
              placeholder="Reason for schedule pin or manual override..."
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="w-full text-xs py-2 px-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          {/* What-If Simulation Output Box */}
          {previewResult && (
            <div
              className={`p-4 rounded-xl border space-y-2 ${
                previewResult.is_valid
                  ? 'bg-emerald-50/80 border-emerald-200 text-emerald-950'
                  : 'bg-amber-50/80 border-amber-200 text-amber-950'
              }`}
            >
              <div className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-brand-600" />
                <span className="text-xs font-extrabold uppercase">Simulation Outcome</span>
              </div>
              <p className="text-xs font-medium leading-relaxed">{previewResult.summary}</p>
              <div className="flex items-center space-x-4 pt-1 text-xs">
                <div>
                  <span className="text-slate-500">Projected Coverage:</span>{' '}
                  <span className="font-extrabold text-slate-900">{previewResult.coverage_percent}%</span>
                </div>
                <div>
                  <span className="text-slate-500">Resolved Gaps:</span>{' '}
                  <span className="font-extrabold text-emerald-700">+{previewResult.resolved_count}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
          <button
            type="button"
            onClick={handleRunWhatIf}
            disabled={isPreviewing}
            className="px-3.5 py-2 rounded-lg text-xs font-semibold bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 transition shadow-xs flex items-center space-x-1.5"
          >
            <Sparkles className="w-3.5 h-3.5 text-brand-600" />
            <span>{isPreviewing ? 'Simulating...' : 'Test Impact (What-If)'}</span>
          </button>

          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-200 transition"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleCommit}
              disabled={isSaving}
              className="px-4 py-2 rounded-lg text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white transition shadow-xs flex items-center space-x-1.5"
            >
              <span>{isSaving ? 'Applying...' : 'Apply Override'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

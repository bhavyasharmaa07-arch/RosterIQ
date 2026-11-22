import React, { useState } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  Filter,
} from 'lucide-react';
import { ConflictData } from '../types';

interface ConflictDrawerProps {
  conflicts: ConflictData[];
  onResolve: (conflictId: number) => Promise<void>;
  isResolving: boolean;
}

export const ConflictDrawer: React.FC<ConflictDrawerProps> = ({
  conflicts,
  onResolve,
  isResolving,
}) => {
  const [filterSeverity, setFilterSeverity] = useState<'all' | 'critical' | 'high' | 'warning'>('all');
  const [resolvingId, setResolvingId] = useState<number | null>(null);

  const filtered = conflicts.filter((c) => {
    if (filterSeverity === 'all') return true;
    return c.severity === filterSeverity;
  });

  const criticalCount = conflicts.filter((c) => c.severity === 'critical').length;
  const highCount = conflicts.filter((c) => c.severity === 'high').length;
  const warningCount = conflicts.filter((c) => c.severity === 'warning').length;

  const handleResolveClick = async (id: number) => {
    setResolvingId(id);
    try {
      await onResolve(id);
    } finally {
      setResolvingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
            <ShieldAlert className="w-5 h-5 text-red-600" />
            <span>Scheduling Conflicts & Automated Resolution Recommendations</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Rule violations detected by the deterministic constraint engine with suggested colleague assignments
          </p>
        </div>

        {/* Severity Tabs */}
        <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-semibold">
          <button
            onClick={() => setFilterSeverity('all')}
            className={`px-3 py-1.5 rounded-md transition ${
              filterSeverity === 'all' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            All ({conflicts.length})
          </button>
          <button
            onClick={() => setFilterSeverity('critical')}
            className={`px-3 py-1.5 rounded-md transition ${
              filterSeverity === 'critical' ? 'bg-red-600 text-white shadow-xs' : 'text-red-700 hover:bg-red-50'
            }`}
          >
            Critical ({criticalCount})
          </button>
          <button
            onClick={() => setFilterSeverity('high')}
            className={`px-3 py-1.5 rounded-md transition ${
              filterSeverity === 'high' ? 'bg-amber-600 text-white shadow-xs' : 'text-amber-700 hover:bg-amber-50'
            }`}
          >
            High ({highCount})
          </button>
          <button
            onClick={() => setFilterSeverity('warning')}
            className={`px-3 py-1.5 rounded-md transition ${
              filterSeverity === 'warning' ? 'bg-slate-700 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Warnings ({warningCount})
          </button>
        </div>
      </div>

      {/* Conflicts List */}
      {filtered.length === 0 ? (
        <div className="bg-white p-12 rounded-xl border border-slate-200 shadow-xs text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">No Conflicts Detected</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            All brand coverage constraints, workload caps, and operating calendars are fully satisfied for the selected filter.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filtered.map((conflict) => {
            const isCritical = conflict.severity === 'critical';
            const isHigh = conflict.severity === 'high';

            return (
              <div
                key={conflict.id}
                className={`bg-white rounded-xl border shadow-xs p-5 transition hover:shadow-sm ${
                  isCritical
                    ? 'border-red-200'
                    : isHigh
                    ? 'border-amber-200'
                    : 'border-slate-200'
                }`}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center space-x-2">
                      <span
                        className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full ${
                          isCritical
                            ? 'bg-red-100 text-red-800'
                            : isHigh
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        {conflict.severity}
                      </span>
                      <span className="text-xs font-mono font-semibold text-slate-500">
                        {conflict.conflict_type.replace('_', ' ').toUpperCase()}
                      </span>
                      {conflict.date && (
                        <span className="text-xs font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
                          📅 {new Date(conflict.date).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })}
                        </span>
                      )}
                    </div>

                    <h4 className="text-sm font-bold text-slate-900">
                      {conflict.brand_name && `${conflict.brand_name} • `}
                      {conflict.process_name && `${conflict.process_name}`}
                    </h4>

                    <p className="text-xs text-slate-700 leading-relaxed font-medium">
                      {conflict.explanation}
                    </p>
                  </div>

                  {/* Suggestion & Action Button */}
                  {conflict.suggestion && (
                    <div className="bg-brand-50/70 border border-brand-200 rounded-xl p-3.5 max-w-md w-full lg:w-auto flex flex-col justify-between space-y-3">
                      <div className="flex items-start space-x-2">
                        <Sparkles className="w-4 h-4 text-brand-600 mt-0.5 shrink-0" />
                        <div>
                          <span className="text-[11px] font-bold text-brand-900 uppercase">Engine Recommendation</span>
                          <p className="text-xs text-brand-800 mt-0.5">{conflict.suggestion}</p>
                        </div>
                      </div>

                      {conflict.suggestion_action && (
                        <button
                          onClick={() => handleResolveClick(conflict.id)}
                          disabled={isResolving}
                          className="self-end px-3 py-1.5 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-xs font-semibold shadow-xs transition flex items-center space-x-1.5 disabled:bg-brand-400"
                        >
                          <span>{resolvingId === conflict.id ? 'Resolving...' : 'Authorize & Assign'}</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

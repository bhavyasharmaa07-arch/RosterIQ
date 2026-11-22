import React from 'react';
import {
  Calendar,
  Layers,
  ShieldAlert,
  Download,
  RefreshCw,
  LayoutDashboard,
  CheckCircle2,
  AlertCircle,
  FileSpreadsheet,
} from 'lucide-react';

interface HeaderProps {
  currentTab: 'dashboard' | 'roster' | 'coverage' | 'conflicts' | 'leaves';
  onTabChange: (tab: 'dashboard' | 'roster' | 'coverage' | 'conflicts' | 'leaves') => void;
  year: number;
  month: number;
  onMonthChange: (year: number, month: number) => void;
  onRegenerate: () => void;
  isGenerating: boolean;
  exportUrl: string;
  conflictCount: number;
  rosterStatus: string;
  coveragePercent: number;
}

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  onTabChange,
  year,
  month,
  onMonthChange,
  onRegenerate,
  isGenerating,
  exportUrl,
  conflictCount,
  rosterStatus,
  coveragePercent,
}) => {
  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const handlePrevMonth = () => {
    if (month === 1) onMonthChange(year - 1, 12);
    else onMonthChange(year, month - 1);
  };

  const handleNextMonth = () => {
    if (month === 12) onMonthChange(year + 1, 1);
    else onMonthChange(year, month + 1);
  };

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-700 via-brand-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold tracking-tight text-slate-900">Roster<span className="text-brand-600">IQ</span></span>
                <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
                  DataStraw CX Ops
                </span>
              </div>
              <p className="text-xs text-slate-500">Autonomous Pod Workforce Rostering & Shift Management</p>
            </div>
          </div>

          {/* Month Selector & Status Badge */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200">
              <button
                onClick={handlePrevMonth}
                className="px-2 py-1 text-slate-600 hover:text-slate-900 hover:bg-white rounded transition text-xs font-semibold"
                title="Previous Month"
              >
                ◀
              </button>
              <span className="px-3 py-1 font-semibold text-slate-800 text-sm">
                {monthNames[month - 1]} {year}
              </span>
              <button
                onClick={handleNextMonth}
                className="px-2 py-1 text-slate-600 hover:text-slate-900 hover:bg-white rounded transition text-xs font-semibold"
                title="Next Month"
              >
                ▶
              </button>
            </div>

            {/* Health Pill */}
            <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 rounded-lg border text-xs font-medium bg-slate-50 border-slate-200">
              {rosterStatus === 'valid' ? (
                <div className="flex items-center space-x-1.5 text-emerald-700">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Compliant ({coveragePercent}%)</span>
                </div>
              ) : rosterStatus === 'partial' ? (
                <div className="flex items-center space-x-1.5 text-amber-700">
                  <AlertCircle className="w-4 h-4 text-amber-600" />
                  <span>Partial ({coveragePercent}%)</span>
                </div>
              ) : (
                <span className="text-slate-500">Not Generated</span>
              )}
            </div>

            {/* Action Buttons */}
            <button
              onClick={onRegenerate}
              disabled={isGenerating}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white transition shadow-sm ${
                isGenerating ? 'bg-brand-400 cursor-not-allowed' : 'bg-brand-600 hover:bg-brand-700'
              }`}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isGenerating ? 'animate-spin' : ''}`} />
              <span>{isGenerating ? 'Generating...' : 'Solve & Generate'}</span>
            </button>

            <a
              href={exportUrl}
              download
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 hover:text-slate-900 transition shadow-sm"
              title="Download full schedule as Excel (.xlsx)"
            >
              <Download className="w-3.5 h-3.5 text-emerald-600" />
              <span className="hidden sm:inline">Export Excel</span>
            </a>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 border-t border-slate-100 overflow-x-auto py-1">
          <button
            onClick={() => onTabChange('dashboard')}
            className={`flex items-center space-x-2 px-3.5 py-2 text-xs font-medium rounded-lg transition-colors whitespace-nowrap ${
              currentTab === 'dashboard'
                ? 'bg-brand-50 text-brand-700 font-semibold shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <LayoutDashboard className="w-4 h-4" />
            <span>Executive Dashboard</span>
          </button>

          <button
            onClick={() => onTabChange('roster')}
            className={`flex items-center space-x-2 px-3.5 py-2 text-xs font-medium rounded-lg transition-colors whitespace-nowrap ${
              currentTab === 'roster'
                ? 'bg-brand-50 text-brand-700 font-semibold shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Calendar className="w-4 h-4" />
            <span>Employee Schedule Matrix</span>
          </button>

          <button
            onClick={() => onTabChange('coverage')}
            className={`flex items-center space-x-2 px-3.5 py-2 text-xs font-medium rounded-lg transition-colors whitespace-nowrap ${
              currentTab === 'coverage'
                ? 'bg-brand-50 text-brand-700 font-semibold shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>Brand Coverage Matrix</span>
          </button>

          <button
            onClick={() => onTabChange('conflicts')}
            className={`flex items-center space-x-2 px-3.5 py-2 text-xs font-medium rounded-lg transition-colors whitespace-nowrap ${
              currentTab === 'conflicts'
                ? 'bg-red-50 text-red-700 font-semibold shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <ShieldAlert className="w-4 h-4 text-red-500" />
            <span>Conflicts & Resolution</span>
            {conflictCount > 0 && (
              <span className="ml-1.5 px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-red-600 text-white">
                {conflictCount}
              </span>
            )}
          </button>

          <button
            onClick={() => onTabChange('leaves')}
            className={`flex items-center space-x-2 px-3.5 py-2 text-xs font-medium rounded-lg transition-colors whitespace-nowrap ${
              currentTab === 'leaves'
                ? 'bg-brand-50 text-brand-700 font-semibold shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <FileSpreadsheet className="w-4 h-4" />
            <span>Leaves & Availability</span>
          </button>
        </div>
      </div>
    </header>
  );
};

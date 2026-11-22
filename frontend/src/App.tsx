import React, { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { DashboardView } from './components/DashboardView';
import { RosterGridView } from './components/RosterGridView';
import { BrandCoverageView } from './components/BrandCoverageView';
import { ConflictDrawer } from './components/ConflictDrawer';
import { WhatIfModal } from './components/WhatIfModal';
import { LeavesView } from './components/LeavesView';
import { api } from './services/api';
import {
  DashboardData,
  RosterViewData,
  ConflictData,
  EmployeeData,
  PodData,
  BrandData,
  LeaveData,
  CellOut,
  DayEditIn,
} from './types';
import { AlertCircle, RefreshCw } from 'lucide-react';

export function App() {
  const [year, setYear] = useState<number>(2026);
  const [month, setMonth] = useState<number>(11);
  const [currentTab, setCurrentTab] = useState<'dashboard' | 'roster' | 'coverage' | 'conflicts' | 'leaves'>('dashboard');

  // Master State
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [rosterView, setRosterView] = useState<RosterViewData | null>(null);
  const [coverageView, setCoverageView] = useState<RosterViewData | null>(null);
  const [conflicts, setConflicts] = useState<ConflictData[]>([]);
  const [employees, setEmployees] = useState<EmployeeData[]>([]);
  const [pods, setPods] = useState<PodData[]>([]);
  const [brands, setBrands] = useState<BrandData[]>([]);
  const [leaves, setLeaves] = useState<LeaveData[]>([]);

  // Filter States
  const [selectedPod, setSelectedPod] = useState<number | null>(null);
  const [selectedBrand, setSelectedBrand] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Async States
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isResolving, setIsResolving] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string>('');

  // What-If Modal State
  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const [modalEmployeeId, setModalEmployeeId] = useState<number>(0);
  const [modalEmployeeName, setModalEmployeeName] = useState<string>('');
  const [modalDate, setModalDate] = useState<string>('');
  const [modalInitialCell, setModalInitialCell] = useState<CellOut | null>(null);

  // Load all foundational data
  const loadData = async (targetYear = year, targetMonth = month) => {
    setIsLoading(true);
    setErrorMsg('');
    try {
      const [
        dashRes,
        rosterRes,
        covRes,
        conflictsRes,
        empsRes,
        podsRes,
        brandsRes,
        leavesRes,
      ] = await Promise.all([
        api.getDashboard(targetYear, targetMonth),
        api.getRoster(targetYear, targetMonth, 'employee', selectedPod, selectedBrand, searchQuery),
        api.getRoster(targetYear, targetMonth, 'coverage', selectedPod, selectedBrand, searchQuery),
        api.getConflicts(targetYear, targetMonth),
        api.getEmployees(),
        api.getPods(),
        api.getBrands(),
        api.getLeaves(),
      ]);

      setDashboard(dashRes);
      setRosterView(rosterRes);
      setCoverageView(covRes);
      setConflicts(conflictsRes);
      setEmployees(empsRes);
      setPods(podsRes);
      setBrands(brandsRes);
      setLeaves(leavesRes);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || 'Failed to connect to RosterIQ backend');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData(year, month);
  }, [year, month, selectedPod, selectedBrand, searchQuery]);

  const handleRegenerate = async () => {
    setIsGenerating(true);
    setErrorMsg('');
    try {
      await api.generateRoster(year, month);
      await loadData(year, month);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to generate roster');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleResolveConflict = async (conflictId: number) => {
    setIsResolving(true);
    setErrorMsg('');
    try {
      await api.resolveConflict(conflictId);
      await loadData(year, month);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to resolve conflict');
    } finally {
      setIsResolving(false);
    }
  };

  const handleOpenWhatIf = (
    employeeId: number,
    employeeName: string,
    dateStr: string,
    cell: CellOut
  ) => {
    setModalEmployeeId(employeeId);
    setModalEmployeeName(employeeName);
    setModalDate(dateStr);
    setModalInitialCell(cell);
    setModalOpen(true);
  };

  const handleApplyOverride = async (payload: DayEditIn) => {
    await api.saveOverride(payload);
    await loadData(year, month);
  };

  const handlePreviewOverride = async (payload: DayEditIn) => {
    return api.previewOverride(payload, year, month);
  };

  const handleUpdateLeaveStatus = async (leaveId: number, status: 'approved' | 'rejected') => {
    await api.updateLeaveStatus(leaveId, status);
    await loadData(year, month);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Header */}
      <Header
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        year={year}
        month={month}
        onMonthChange={(y, m) => {
          setYear(y);
          setMonth(m);
        }}
        onRegenerate={handleRegenerate}
        isGenerating={isGenerating}
        exportUrl={api.getExcelExportUrl(year, month)}
        conflictCount={conflicts.filter((c) => c.severity !== 'warning').length}
        rosterStatus={dashboard?.roster_status || 'not_generated'}
        coveragePercent={dashboard?.coverage_percent || 0}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Error Alert */}
        {errorMsg && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-800 text-xs flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
              <span>{errorMsg}</span>
            </div>
            <button
              onClick={() => loadData(year, month)}
              className="px-2.5 py-1 bg-red-100 hover:bg-red-200 text-red-800 rounded font-semibold transition"
            >
              Retry
            </button>
          </div>
        )}

        {/* Loading Spinner */}
        {isLoading && !dashboard ? (
          <div className="py-24 flex flex-col items-center justify-center space-y-3">
            <RefreshCw className="w-8 h-8 text-brand-600 animate-spin" />
            <p className="text-xs font-semibold text-slate-500">Connecting to RosterIQ Database & Engine...</p>
          </div>
        ) : (
          <>
            {currentTab === 'dashboard' && dashboard && (
              <DashboardView
                data={dashboard}
                onNavigateToConflicts={() => setCurrentTab('conflicts')}
                onNavigateToRoster={() => setCurrentTab('roster')}
              />
            )}

            {currentTab === 'roster' && rosterView && (
              <RosterGridView
                data={rosterView}
                pods={pods}
                brands={brands}
                selectedPod={selectedPod}
                onSelectPod={setSelectedPod}
                selectedBrand={selectedBrand}
                onSelectBrand={setSelectedBrand}
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                onCellClick={handleOpenWhatIf}
              />
            )}

            {currentTab === 'coverage' && coverageView && (
              <BrandCoverageView
                data={coverageView}
                pods={pods}
                selectedPod={selectedPod}
                onSelectPod={setSelectedPod}
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
              />
            )}

            {currentTab === 'conflicts' && (
              <ConflictDrawer
                conflicts={conflicts}
                onResolve={handleResolveConflict}
                isResolving={isResolving}
              />
            )}

            {currentTab === 'leaves' && (
              <LeavesView
                leaves={leaves}
                onUpdateStatus={handleUpdateLeaveStatus}
                isUpdating={isLoading}
              />
            )}
          </>
        )}
      </main>

      {/* What-If Manager Override Modal */}
      <WhatIfModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        employeeId={modalEmployeeId}
        employeeName={modalEmployeeName}
        targetDate={modalDate}
        initialCell={modalInitialCell}
        employees={employees}
        brands={brands}
        onApplyOverride={handleApplyOverride}
        onPreview={handlePreviewOverride}
      />
    </div>
  );
}
export default App;

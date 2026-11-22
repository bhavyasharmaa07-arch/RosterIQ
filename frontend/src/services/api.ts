import {
  DashboardData,
  RosterViewData,
  ConflictData,
  EmployeeData,
  PodData,
  BrandData,
  DayEditIn,
  PreviewData,
  LeaveData,
  RosterSummary,
} from '../types';

const API_BASE = '/api';

export async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    let errMsg = `Request failed: ${res.statusText}`;
    try {
      const err = await res.json();
      if (err.detail) errMsg = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail);
    } catch {}
    throw new Error(errMsg);
  }

  return res.json();
}

export const api = {
  getDashboard: (year: number, month: number) =>
    apiFetch<DashboardData>(`/dashboard?year=${year}&month=${month}`),

  getRoster: (
    year: number,
    month: number,
    view: 'employee' | 'coverage' = 'employee',
    podId?: number | null,
    brandId?: number | null,
    search?: string
  ) => {
    const params = new URLSearchParams({
      year: year.toString(),
      month: month.toString(),
      view,
    });
    if (podId) params.append('pod_id', podId.toString());
    if (brandId) params.append('brand_id', brandId.toString());
    if (search && search.trim()) params.append('search', search.trim());
    return apiFetch<RosterViewData>(`/roster?${params.toString()}`);
  },

  generateRoster: (year: number, month: number) =>
    apiFetch<RosterSummary>('/roster/generate', {
      method: 'POST',
      body: JSON.stringify({ year, month }),
    }),

  getConflicts: (year: number, month: number, severity?: string) => {
    const params = new URLSearchParams({
      year: year.toString(),
      month: month.toString(),
    });
    if (severity && severity !== 'all') params.append('severity', severity);
    return apiFetch<ConflictData[]>(`/conflicts?${params.toString()}`);
  },

  resolveConflict: (conflictId: number) =>
    apiFetch<{ success: boolean; message: string }>(`/conflicts/${conflictId}/resolve`, {
      method: 'POST',
    }),

  previewOverride: (payload: DayEditIn, year: number, month: number) =>
    apiFetch<PreviewData>(`/overrides/preview?year=${year}&month=${month}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  saveOverride: (payload: DayEditIn) =>
    apiFetch<{ success: boolean; message: string }>('/overrides', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  deleteOverride: (employeeId: number, targetDate: string) =>
    apiFetch<{ success: boolean; message: string }>(`/overrides/${employeeId}/${targetDate}`, {
      method: 'DELETE',
    }),

  getEmployees: () => apiFetch<EmployeeData[]>('/employees'),
  getPods: () => apiFetch<PodData[]>('/pods'),
  getBrands: () => apiFetch<BrandData[]>('/brands'),
  getLeaves: () => apiFetch<LeaveData[]>('/leaves'),

  updateLeaveStatus: (leaveId: number, status: 'pending' | 'approved' | 'rejected') =>
    apiFetch<{ success: boolean; message: string }>(`/leaves/${leaveId}/status?status=${status}`, {
      method: 'PATCH',
    }),

  getExcelExportUrl: (year: number, month: number) =>
    `${API_BASE}/roster/export?year=${year}&month=${month}`,
};

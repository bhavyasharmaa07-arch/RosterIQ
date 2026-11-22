export interface AssignmentOut {
  id: number;
  brand_id: number;
  brand_code: string;
  brand_name: string;
  process_id: number;
  process_code: string;
  process_name: string;
  is_primary: boolean;
}

export interface EmployeeData {
  id: number;
  employee_code: string;
  full_name: string;
  email: string;
  pod_id: number;
  pod_name: string;
  pod_code: string;
  designation: string;
  employment_status: 'active' | 'inactive' | 'on_notice';
  availability_status: 'available' | 'unavailable';
  today_status: string;
  weekly_off_preference: number;
  weekly_offs: number[];
  avoid_weekdays: number[];
  max_daily_workload: number;
  notes: string;
  is_pod_lead: boolean;
  assignments: AssignmentOut[];
}

export interface PodData {
  id: number;
  code: string;
  name: string;
  lead_id: number | null;
  lead_name: string | null;
  lead_code: string | null;
  notes: string;
  employee_count: number;
  employees: { id: number; name: string; code: string; role: string }[];
  brands: { id: number; name: string; code: string }[];
}

export interface RuleOut {
  id: number;
  process_id: number;
  process_code: string;
  process_name: string;
  mode: string;
  custom_weekdays: number[];
  holiday_policy: string;
  min_staff: number;
}

export interface BrandData {
  id: number;
  code: string;
  name: string;
  pod_id: number;
  pod_name: string;
  description: string;
  employee_count: number;
  employees: { id: number; name: string; code: string }[];
  rules: RuleOut[];
}

export interface HolidayOut {
  id: number;
  date: string;
  name: string;
}

export interface CellOut {
  date: string;
  status: 'working' | 'weekly_off' | 'approved_leave' | 'comp_off' | 'public_holiday' | 'unavailable' | 'available' | 'calendar_off';
  brands: string[];
  processes: string[];
  brand_ids: number[];
  on_public_holiday: boolean;
  has_gap: boolean;
}

export interface RosterRow {
  employee_id: number;
  employee_code: string;
  full_name: string;
  pod_id: number;
  pod_name: string;
  is_pod_lead: boolean;
  designation: string;
  cells: CellOut[];
}

export interface CoverageCell {
  date: string;
  state: 'covered' | 'gap' | 'closed';
  required: number;
  assigned: number;
  employees: string[];
}

export interface CoverageRow {
  brand_id: number;
  brand_name: string;
  process_id: number;
  process_name: string;
  process_code: string;
  cells: CoverageCell[];
}

export interface RosterSummary {
  id: number;
  year: number;
  month: number;
  status: 'valid' | 'partial' | 'not_generated';
  is_valid: boolean;
  coverage_percent: number;
  conflict_count: number;
  warning_count: number;
  generated_at: string;
}

export interface RosterViewData {
  roster: RosterSummary | null;
  year: number;
  month: number;
  days: string[];
  holidays: HolidayOut[];
  rows: RosterRow[];
  coverage_rows: CoverageRow[];
  view: 'employee' | 'coverage';
}

export interface ConflictData {
  id: number;
  severity: 'critical' | 'high' | 'warning';
  conflict_type: string;
  employee_id: number | null;
  employee_name: string | null;
  employee_code: string | null;
  brand_id: number | null;
  brand_name: string | null;
  process_id: number | null;
  process_name: string | null;
  date: string | null;
  explanation: string;
  suggestion: string;
  suggestion_action: {
    type: string;
    employee_id: number;
    brand_id: number;
    process_id: number;
    date: string;
  } | null;
}

export interface AuditData {
  id: number;
  created_at: string;
  action: string;
  entity: string;
  detail: string;
}

export interface DashboardData {
  year: number;
  month: number;
  total_employees: number;
  active_employees: number;
  total_brands: number;
  total_pods: number;
  total_processes: number;
  roster_status: string;
  is_valid: boolean;
  coverage_percent: number;
  unresolved_conflicts: number;
  warning_count: number;
  employees_on_leave: number;
  on_leave: {
    id: number;
    employee_id: number;
    employee_name: string;
    employee_code: string;
    pod_name: string;
    start_date: string;
    end_date: string;
    leave_type: string;
    reason: string;
  }[];
  upcoming_weekly_offs: {
    day_number: number;
    day_name: string;
    employee_count: number;
  }[];
  brand_coverage: {
    id: number;
    name: string;
    coverage: number;
    met: number;
    total: number;
  }[];
  status_mix: {
    name: string;
    key: string;
    value: number;
  }[];
  recent_changes: AuditData[];
}

export interface DayEditIn {
  employee_id: number;
  date: string;
  status: 'working' | 'weekly_off' | 'approved_leave' | 'comp_off' | 'unavailable' | 'available';
  brand_ids: number[];
  note: string;
  authorise: boolean;
}

export interface PreviewData {
  summary: string;
  requires_confirmation: boolean;
  is_valid: boolean;
  coverage_percent: number;
  new_conflicts: ConflictData[];
  resolved_count: number;
}

export interface LeaveData {
  id: number;
  employee_id: number;
  employee_code: string;
  employee_name: string;
  start_date: string;
  end_date: string;
  leave_type: string;
  status: 'pending' | 'approved' | 'rejected';
  reason: string;
}

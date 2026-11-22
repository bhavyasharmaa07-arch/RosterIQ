"""Pydantic request and response models."""

from __future__ import annotations

from datetime import date as dt_date, datetime as dt_datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

EmploymentStatus = Literal["active", "inactive", "on_notice"]
AvailabilityFlag = Literal["available", "unavailable"]
LeaveStatus = Literal["pending", "approved", "rejected"]
LeaveType = Literal["planned", "sick", "personal"]
RuleMode = Literal["all_days", "holidays_off", "sundays_and_holidays_off", "custom"]
HolidayPolicy = Literal["off", "work"]
DayStatus = Literal["working", "weekly_off", "approved_leave", "comp_off", "unavailable", "available"]


def _clean_email(value: str) -> str:
    email = value.strip().lower()
    if "@" not in email or email.startswith("@") or email.endswith("@") or " " in email:
        raise ValueError("Enter a valid email address")
    local, _, domain = email.partition("@")
    if not local or "." not in domain:
        raise ValueError("Enter a valid email address")
    return email


class AssignmentIn(BaseModel):
    brand_id: int
    process_id: int
    is_primary: bool = True


class AssignmentOut(BaseModel):
    id: int
    brand_id: int
    brand_code: str
    brand_name: str
    process_id: int
    process_code: str
    process_name: str
    is_primary: bool


class EmployeeIn(BaseModel):
    employee_code: str = Field(min_length=2, max_length=32)
    full_name: str = Field(min_length=2, max_length=160)
    email: str
    pod_id: int
    designation: str = Field(min_length=2, max_length=120)
    employment_status: EmploymentStatus = "active"
    availability_status: AvailabilityFlag = "available"
    weekly_off_preference: int = Field(ge=0, le=6)
    weekly_offs: list[int] = Field(default_factory=list)
    avoid_weekdays: list[int] = Field(default_factory=list)
    max_daily_workload: int = Field(ge=1, le=6)
    notes: str = ""
    assignments: list[AssignmentIn] = Field(default_factory=list)

    @field_validator("email")
    @classmethod
    def email_ok(cls, value: str) -> str:
        return _clean_email(value)

    @field_validator("employee_code")
    @classmethod
    def code_ok(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("weekly_offs", "avoid_weekdays")
    @classmethod
    def weekdays_ok(cls, value: list[int]) -> list[int]:
        if any(day < 0 or day > 6 for day in value):
            raise ValueError("Weekdays must be between 0 (Monday) and 6 (Sunday)")
        return sorted(set(value))


class EmployeeOut(BaseModel):
    id: int
    employee_code: str
    full_name: str
    email: str
    pod_id: int
    pod_name: str
    pod_code: str
    designation: str
    employment_status: str
    availability_status: str
    today_status: str
    weekly_off_preference: int
    weekly_offs: list[int]
    avoid_weekdays: list[int]
    max_daily_workload: int
    notes: str
    is_pod_lead: bool
    assignments: list[AssignmentOut]


class PodIn(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=120)
    lead_id: int | None = None
    notes: str = ""

    @field_validator("code")
    @classmethod
    def code_ok(cls, value: str) -> str:
        return value.strip().upper()


class PodOut(BaseModel):
    id: int
    code: str
    name: str
    lead_id: int | None
    lead_name: str | None
    lead_code: str | None
    notes: str
    employee_count: int
    employees: list[dict[str, Any]]
    brands: list[dict[str, Any]]


class ProcessIn(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=160)
    description: str = ""

    @field_validator("code")
    @classmethod
    def code_ok(cls, value: str) -> str:
        return value.strip().upper()


class ProcessOut(BaseModel):
    id: int
    code: str
    name: str
    description: str
    is_predefined: bool
    assignment_count: int


class BrandIn(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=160)
    pod_id: int
    description: str = ""

    @field_validator("code")
    @classmethod
    def code_ok(cls, value: str) -> str:
        return value.strip().upper()


class RuleOut(BaseModel):
    id: int
    process_id: int
    process_code: str
    process_name: str
    mode: str
    custom_weekdays: list[int]
    holiday_policy: str
    min_staff: int


class BrandOut(BaseModel):
    id: int
    code: str
    name: str
    pod_id: int
    pod_name: str
    description: str
    employee_count: int
    employees: list[dict[str, Any]]
    rules: list[RuleOut]


class RuleIn(BaseModel):
    process_id: int
    mode: RuleMode
    custom_weekdays: list[int] = Field(default_factory=list)
    holiday_policy: HolidayPolicy = "off"
    min_staff: int = Field(ge=0, le=20)

    @field_validator("custom_weekdays")
    @classmethod
    def weekdays_ok(cls, value: list[int]) -> list[int]:
        if any(day < 0 or day > 6 for day in value):
            raise ValueError("Weekdays must be between 0 and 6")
        return sorted(set(value))


class HolidayIn(BaseModel):
    date: dt_date
    name: str = Field(min_length=2, max_length=160)


class HolidayOut(BaseModel):
    id: int
    date: dt_date
    name: str


class LeaveIn(BaseModel):
    employee_id: int
    start_date: dt_date
    end_date: dt_date
    leave_type: LeaveType = "planned"
    status: LeaveStatus = "pending"
    reason: str = ""

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, value: dt_date, info) -> dt_date:  # type: ignore[no-untyped-def]
        start = info.data.get("start_date")
        if start and value < start:
            raise ValueError("End date cannot be before the start date")
        return value


class LeaveOut(BaseModel):
    id: int
    employee_id: int
    employee_code: str
    employee_name: str
    start_date: dt_date
    end_date: dt_date
    leave_type: str
    status: str
    reason: str


class CompOffIn(BaseModel):
    employee_id: int
    off_date: dt_date
    worked_date: dt_date | None = None
    status: LeaveStatus = "pending"
    reason: str = ""


class CompOffOut(BaseModel):
    id: int
    employee_id: int
    employee_code: str
    employee_name: str
    off_date: dt_date
    worked_date: dt_date | None
    status: str
    reason: str


class AvailabilityIn(BaseModel):
    employee_id: int
    date: dt_date
    status: Literal["unavailable", "preferred_off"]
    note: str = ""


class AvailabilityOut(BaseModel):
    id: int
    employee_id: int
    employee_code: str
    employee_name: str
    date: dt_date
    status: str
    note: str


class WeeklyOffIn(BaseModel):
    employee_id: int
    days: list[int]

    @field_validator("days")
    @classmethod
    def weekdays_ok(cls, value: list[int]) -> list[int]:
        if any(day < 0 or day > 6 for day in value):
            raise ValueError("Weekdays must be between 0 and 6")
        return sorted(set(value))


class GenerateIn(BaseModel):
    year: int = Field(ge=2024, le=2100)
    month: int = Field(ge=1, le=12)


class ConflictOut(BaseModel):
    id: int
    severity: str
    conflict_type: str
    employee_id: int | None = None
    employee_name: str | None = None
    employee_code: str | None = None
    brand_id: int | None = None
    brand_name: str | None = None
    process_id: int | None = None
    process_name: str | None = None
    date: dt_date | None = None
    explanation: str
    suggestion: str = ""
    suggestion_action: dict[str, Any] | None = None


class RosterSummary(BaseModel):
    id: int
    year: int
    month: int
    status: str
    is_valid: bool
    coverage_percent: float
    conflict_count: int
    warning_count: int
    generated_at: dt_datetime


class CellOut(BaseModel):
    date: dt_date
    status: str
    brands: list[str]
    processes: list[str]
    brand_ids: list[int]
    on_public_holiday: bool
    has_gap: bool


class RosterRow(BaseModel):
    employee_id: int
    employee_code: str
    full_name: str
    pod_id: int
    pod_name: str
    is_pod_lead: bool
    designation: str
    cells: list[CellOut]


class CoverageCell(BaseModel):
    date: dt_date
    state: str
    required: int
    assigned: int
    employees: list[str]


class CoverageRow(BaseModel):
    brand_id: int
    brand_name: str
    process_id: int
    process_name: str
    process_code: str
    cells: list[CoverageCell]


class RosterView(BaseModel):
    roster: RosterSummary | None
    year: int
    month: int
    days: list[dt_date]
    holidays: list[HolidayOut]
    rows: list[RosterRow] = Field(default_factory=list)
    coverage_rows: list[CoverageRow] = Field(default_factory=list)
    view: str


class DayEditIn(BaseModel):
    employee_id: int
    date: dt_date
    status: DayStatus
    brand_ids: list[int] = Field(default_factory=list)
    note: str = ""
    authorise: bool = False


class PreviewOut(BaseModel):
    summary: str
    requires_confirmation: bool
    is_valid: bool
    coverage_percent: float
    new_conflicts: list[ConflictOut]
    resolved_count: int


class AuditOut(BaseModel):
    id: int
    created_at: dt_datetime
    action: str
    entity: str
    detail: str


class DashboardOut(BaseModel):
    year: int
    month: int
    total_employees: int
    active_employees: int
    total_brands: int
    total_pods: int
    total_processes: int
    roster_status: str
    is_valid: bool
    coverage_percent: float
    unresolved_conflicts: int
    warning_count: int
    employees_on_leave: int
    on_leave: list[dict[str, Any]]
    upcoming_weekly_offs: list[dict[str, Any]]
    brand_coverage: list[dict[str, Any]]
    status_mix: list[dict[str, Any]]
    recent_changes: list[AuditOut]

"""Deterministic constraint-aware roster generator.

The unit of work is a brand-day, not a process-shift. An employee assigned to
several processes of the same brand covers all of those processes that operate
that day, and that counts as one brand toward the daily workload limit.

Mandatory constraints are never relaxed. Preferences, fairness and unpopular
shifts only change who is chosen when several people can legally work.
If demand cannot be met, the best feasible assignment is kept and each gap is
returned as a conflict. A roster with any critical or high conflict is partial,
never valid.
"""

from __future__ import annotations

import calendar
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy.orm import Session, selectinload

from app.models import (
    Brand,
    CompOff,
    CoverageRequirement,
    Employee,
    EmployeeAssignment,
    EmployeeAvailability,
    Leave,
    Process,
    PublicHoliday,
    Roster,
    RosterAssignment,
    RosterEntry,
    RosterOverride,
    SchedulingConflict,
    WeeklyOff,
    WorkingRule,
    utcnow,
)

SEVERITY_RANK = {"critical": 0, "high": 1, "warning": 2}
BLOCK_LABELS = {
    "approved_leave": "approved leave",
    "comp_off": "an approved comp-off",
    "weekly_off": "their weekly off",
    "unavailable": "marked unavailable",
    "inactive": "not an active employee",
}


@dataclass
class Hypothetical:
    """In-memory changes used to preview a manager action before saving it."""

    extra_leave_days: dict[int, set[date]] = field(default_factory=lambda: defaultdict(set))
    extra_compoff_days: dict[int, set[date]] = field(default_factory=lambda: defaultdict(set))
    replace_weekly_offs: dict[int, set[int]] = field(default_factory=dict)
    extra_unavailable: dict[int, set[date]] = field(default_factory=lambda: defaultdict(set))
    extra_preferred: dict[int, set[date]] = field(default_factory=lambda: defaultdict(set))
    extra_assignments: list[tuple[int, int, int, bool]] = field(default_factory=list)
    # (employee_id, date) -> (status, brand ids)
    extra_overrides: dict[tuple[int, date], tuple[str, list[int]]] = field(default_factory=dict)
    ignore_override_keys: set[tuple[int, date]] = field(default_factory=set)


@dataclass
class SlotResult:
    day: date
    brand_id: int
    process_id: int
    need: int
    have: int


@dataclass
class SolveResult:
    year: int
    month: int
    days: list[date]
    status_by_emp_day: dict[tuple[int, date], str]
    brands_by_emp_day: dict[tuple[int, date], list[int]]
    holiday_dates: set[date]
    conflicts: list[dict]
    slots: list[SlotResult]
    coverage_percent: float
    is_valid: bool


def month_days(year: int, month: int) -> list[date]:
    count = calendar.monthrange(year, month)[1]
    return [date(year, month, day) for day in range(1, count + 1)]


def parse_weekdays(raw: str | None) -> set[int]:
    if not raw:
        return set()
    days = set()
    for part in raw.split(","):
        part = part.strip()
        if part == "":
            continue
        days.add(int(part))
    return days


def operates(mode: str, custom_weekdays: str, holiday_policy: str, day: date, holidays: set[date]) -> bool:
    holiday = day in holidays
    dow = day.weekday()
    if mode == "all_days":
        return True
    if mode == "holidays_off":
        return not holiday
    if mode == "sundays_and_holidays_off":
        return dow != 6 and not holiday
    if mode == "custom":
        if dow not in parse_weekdays(custom_weekdays):
            return False
        if holiday and holiday_policy != "work":
            return False
        return True
    return dow != 6 and not holiday


def _daterange(start: date, end: date) -> list[date]:
    days = []
    cursor = start
    while cursor <= end:
        days.append(cursor)
        cursor += timedelta(days=1)
    return days


@dataclass
class Context:
    year: int
    month: int
    days: list[date]
    holidays: set[date]
    holiday_names: dict[date, str]
    employees: dict[int, Employee]
    brands: dict[int, Brand]
    processes: dict[int, Process]
    rules: dict[tuple[int, int], WorkingRule]
    coverage: dict[tuple[int, int, int], int]
    # (employee, brand, process) -> is_primary
    assignment_flag: dict[tuple[int, int, int], bool]
    emp_brand_processes: dict[tuple[int, int], set[int]]
    brand_process_emps: dict[tuple[int, int], list[tuple[int, bool]]]
    weekly_offs: dict[int, set[int]]
    leave_days: dict[int, set[date]]
    compoff_days: dict[int, set[date]]
    unavailable_days: dict[int, set[date]]
    preferred_days: dict[int, set[date]]
    overrides: dict[tuple[int, date], tuple[str, list[int]]]
    avoid: dict[int, set[int]]
    pod_of: dict[int, int]


def load_context(db: Session, year: int, month: int, hypo: Hypothetical | None = None) -> Context:
    hypo = hypo or Hypothetical()
    days = month_days(year, month)
    day_set = set(days)
    employees = {
        emp.id: emp
        for emp in db.query(Employee).options(selectinload(Employee.pod)).all()
    }
    brands = {brand.id: brand for brand in db.query(Brand).all()}
    processes = {process.id: process for process in db.query(Process).all()}
    rules = {(rule.brand_id, rule.process_id): rule for rule in db.query(WorkingRule).all()}
    coverage: dict[tuple[int, int, int], int] = {}
    for row in db.query(CoverageRequirement).all():
        coverage[(row.brand_id, row.process_id, row.day_of_week)] = row.min_staff

    assignment_flag: dict[tuple[int, int, int], bool] = {}
    emp_brand_processes: dict[tuple[int, int], set[int]] = defaultdict(set)
    brand_process_emps: dict[tuple[int, int], list[tuple[int, bool]]] = defaultdict(list)
    for row in db.query(EmployeeAssignment).all():
        assignment_flag[(row.employee_id, row.brand_id, row.process_id)] = row.is_primary
        emp_brand_processes[(row.employee_id, row.brand_id)].add(row.process_id)
        brand_process_emps[(row.brand_id, row.process_id)].append((row.employee_id, row.is_primary))
    for emp_id, brand_id, process_id, is_primary in hypo.extra_assignments:
        key = (emp_id, brand_id, process_id)
        if key in assignment_flag:
            continue
        assignment_flag[key] = is_primary
        emp_brand_processes[(emp_id, brand_id)].add(process_id)
        brand_process_emps[(brand_id, process_id)].append((emp_id, is_primary))

    weekly_offs: dict[int, set[int]] = defaultdict(set)
    for row in db.query(WeeklyOff).all():
        weekly_offs[row.employee_id].add(row.day_of_week)
    for emp_id, days_off in hypo.replace_weekly_offs.items():
        weekly_offs[emp_id] = set(days_off)

    leave_days: dict[int, set[date]] = defaultdict(set)
    for row in db.query(Leave).filter(Leave.status == "approved").all():
        for day in _daterange(row.start_date, row.end_date):
            if day in day_set:
                leave_days[row.employee_id].add(day)
    for emp_id, extra in hypo.extra_leave_days.items():
        leave_days[emp_id].update(day for day in extra if day in day_set)

    compoff_days: dict[int, set[date]] = defaultdict(set)
    for row in db.query(CompOff).filter(CompOff.status == "approved").all():
        if row.off_date in day_set:
            compoff_days[row.employee_id].add(row.off_date)
    for emp_id, extra in hypo.extra_compoff_days.items():
        compoff_days[emp_id].update(day for day in extra if day in day_set)

    unavailable_days: dict[int, set[date]] = defaultdict(set)
    preferred_days: dict[int, set[date]] = defaultdict(set)
    for row in db.query(EmployeeAvailability).all():
        if row.date not in day_set:
            continue
        if row.status == "unavailable":
            unavailable_days[row.employee_id].add(row.date)
        elif row.status == "preferred_off":
            preferred_days[row.employee_id].add(row.date)
    for emp_id, extra in hypo.extra_unavailable.items():
        unavailable_days[emp_id].update(day for day in extra if day in day_set)
    for emp_id, extra in hypo.extra_preferred.items():
        preferred_days[emp_id].update(day for day in extra if day in day_set)

    overrides: dict[tuple[int, date], tuple[str, list[int]]] = {}
    for row in db.query(RosterOverride).all():
        if row.date not in day_set or (row.employee_id, row.date) in hypo.ignore_override_keys:
            continue
        brand_ids = [int(part) for part in row.brand_ids.split(",") if part.strip()]
        overrides[(row.employee_id, row.date)] = (row.status, brand_ids)
    for key, value in hypo.extra_overrides.items():
        if key[1] in day_set:
            overrides[key] = value

    holidays = {row.date: row.name for row in db.query(PublicHoliday).all()}
    avoid = {emp.id: parse_weekdays(emp.avoid_weekdays) for emp in employees.values()}

    return Context(
        year=year,
        month=month,
        days=days,
        holidays=set(holidays),
        holiday_names=holidays,
        employees=employees,
        brands=brands,
        processes=processes,
        rules=rules,
        coverage=coverage,
        assignment_flag=assignment_flag,
        emp_brand_processes=emp_brand_processes,
        brand_process_emps=brand_process_emps,
        weekly_offs=weekly_offs,
        leave_days=leave_days,
        compoff_days=compoff_days,
        unavailable_days=unavailable_days,
        preferred_days=preferred_days,
        overrides=overrides,
        avoid=avoid,
        pod_of={emp.id: emp.pod_id for emp in employees.values()},
    )


def min_staff(ctx: Context, brand_id: int, process_id: int, day: date) -> int:
    specific = ctx.coverage.get((brand_id, process_id, day.weekday()))
    if specific is not None:
        return specific
    general = ctx.coverage.get((brand_id, process_id, -1))
    if general is not None:
        return general
    return 1


def rule_operates(ctx: Context, brand_id: int, process_id: int, day: date) -> bool:
    rule = ctx.rules.get((brand_id, process_id))
    if rule is None:
        return operates("sundays_and_holidays_off", "", "off", day, ctx.holidays)
    return operates(rule.mode, rule.custom_weekdays, rule.holiday_policy, day, ctx.holidays)


def block_reason(ctx: Context, emp_id: int, day: date) -> str | None:
    emp = ctx.employees.get(emp_id)
    if emp is None or emp.employment_status != "active":
        return "inactive"
    if emp.availability_status == "unavailable":
        return "unavailable"
    if day in ctx.unavailable_days[emp_id]:
        return "unavailable"
    if day in ctx.leave_days[emp_id]:
        return "approved_leave"
    if day in ctx.compoff_days[emp_id]:
        return "comp_off"
    if day.weekday() in ctx.weekly_offs[emp_id]:
        return "weekly_off"
    override = ctx.overrides.get((emp_id, day))
    if override and override[0] in {"weekly_off", "approved_leave", "comp_off", "unavailable"}:
        return override[0]
    return None


def _names(ctx: Context, emp_id: int) -> str:
    emp = ctx.employees[emp_id]
    return f"{emp.full_name} ({emp.employee_code})"


def solve(db: Session, year: int, month: int, hypo: Hypothetical | None = None) -> SolveResult:
    ctx = load_context(db, year, month, hypo)
    scheduled: dict[tuple[int, date], set[int]] = defaultdict(set)
    covered: dict[tuple[date, int, int], set[int]] = defaultdict(set)
    conflicts: list[dict] = []
    working_days: dict[int, int] = defaultdict(int)
    unpopular_days: dict[int, int] = defaultdict(int)

    def add_conflict(**payload) -> None:
        conflicts.append(payload)

    def credit(emp_id: int, day: date, brand_id: int) -> bool:
        if block_reason(ctx, emp_id, day):
            return False
        current = scheduled[(emp_id, day)]
        if brand_id in current:
            return True
        limit = ctx.employees[emp_id].max_daily_workload
        if len(current) >= limit:
            return False
        first_brand_today = len(current) == 0
        current.add(brand_id)
        if first_brand_today:
            working_days[emp_id] += 1
            if day.weekday() == 6 or day in ctx.holidays:
                unpopular_days[emp_id] += 1
        for process_id in ctx.emp_brand_processes.get((emp_id, brand_id), set()):
            if rule_operates(ctx, brand_id, process_id, day):
                covered[(day, brand_id, process_id)].add(emp_id)
        return True

    # Manager pins are applied first, but never through a mandatory constraint.
    for (emp_id, day), (status, brand_ids) in sorted(ctx.overrides.items(), key=lambda item: (item[0][1], item[0][0])):
        if status != "working":
            continue
        reason = block_reason(ctx, emp_id, day)
        if reason:
            add_conflict(
                severity="high",
                conflict_type="incompatible_shift",
                employee_id=emp_id,
                brand_id=brand_ids[0] if brand_ids else None,
                process_id=None,
                date=day,
                explanation=(
                    f"{_names(ctx, emp_id)} was pinned to work on {day.isoformat()}, "
                    f"which conflicts with {BLOCK_LABELS.get(reason, reason)}. The pin was not applied."
                ),
                suggestion="Remove the manual working pin or clear the leave, comp-off or weekly off first.",
                suggestion_action=None,
            )
            continue
        for brand_id in brand_ids:
            processes = ctx.emp_brand_processes.get((emp_id, brand_id), set())
            if not processes:
                add_conflict(
                    severity="critical",
                    conflict_type="assignment_violation",
                    employee_id=emp_id,
                    brand_id=brand_id,
                    process_id=None,
                    date=day,
                    explanation=(
                        f"{_names(ctx, emp_id)} cannot be scheduled on {ctx.brands[brand_id].name} "
                        f"on {day.isoformat()} because they are not authorised for any of its processes."
                    ),
                    suggestion="Authorise the employee for the required process, or choose someone who is already authorised.",
                    suggestion_action=None,
                )
                continue
            if not credit(emp_id, day, brand_id):
                add_conflict(
                    severity="high",
                    conflict_type="workload_limit",
                    employee_id=emp_id,
                    brand_id=brand_id,
                    process_id=None,
                    date=day,
                    explanation=(
                        f"{_names(ctx, emp_id)} is already at the daily workload limit of "
                        f"{ctx.employees[emp_id].max_daily_workload} brand(s) on {day.isoformat()}. "
                        f"{ctx.brands[brand_id].name} was not added."
                    ),
                    suggestion="Raise the daily workload limit or move one of the other brands to a different person.",
                    suggestion_action=None,
                )

    slots: list[tuple] = []
    pairs = set(ctx.brand_process_emps) | set(ctx.rules) | {(brand_id, process_id) for brand_id, process_id, _dow in ctx.coverage}
    for brand_id, process_id in pairs:
        if brand_id not in ctx.brands or process_id not in ctx.processes:
            continue
        people = ctx.brand_process_emps.get((brand_id, process_id), [])
        for day in ctx.days:
            if not rule_operates(ctx, brand_id, process_id, day):
                continue
            need = min_staff(ctx, brand_id, process_id, day)
            if need <= 0:
                continue
            eligible = 0
            for emp_id, _primary in people:
                if block_reason(ctx, emp_id, day):
                    continue
                brands_today = scheduled[(emp_id, day)]
                limit = ctx.employees[emp_id].max_daily_workload
                if brand_id not in brands_today and len(brands_today) >= limit:
                    continue
                eligible += 1
            slots.append(
                (
                    eligible,
                    day,
                    ctx.brands[brand_id].code,
                    ctx.processes[process_id].code,
                    brand_id,
                    process_id,
                    need,
                )
            )
    slots.sort()

    for _eligible, day, _bcode, _pcode, brand_id, process_id, need in slots:
        key = (day, brand_id, process_id)
        if len(covered[key]) >= need:
            continue
        candidates = []
        for emp_id, is_primary in ctx.brand_process_emps[(brand_id, process_id)]:
            if emp_id in covered[key]:
                continue
            if block_reason(ctx, emp_id, day):
                continue
            brands_today = scheduled[(emp_id, day)]
            limit = ctx.employees[emp_id].max_daily_workload
            if brand_id not in brands_today and len(brands_today) >= limit:
                continue
            avoid_hit = day.weekday() in ctx.avoid[emp_id] or day in ctx.preferred_days[emp_id]
            unpopular_key = unpopular_days[emp_id] if (day.weekday() == 6 or day in ctx.holidays) else 0
            candidates.append(
                (
                    0 if is_primary else 1,
                    1 if avoid_hit else 0,
                    unpopular_key,
                    working_days[emp_id],
                    ctx.employees[emp_id].employee_code,
                    emp_id,
                )
            )
        candidates.sort()
        for _primary, _avoid, _unpop, _worked, _code, emp_id in candidates:
            if len(covered[key]) >= need:
                break
            credit(emp_id, day, brand_id)

    slot_results: list[SlotResult] = []
    demand = 0
    filled = 0
    for _eligible, day, _bcode, _pcode, brand_id, process_id, need in slots:
        have = len(covered[(day, brand_id, process_id)])
        slot_results.append(SlotResult(day, brand_id, process_id, need, have))
        demand += need
        filled += min(have, need)
        if have >= need:
            continue
        _record_gap(ctx, conflicts, day, brand_id, process_id, need, have, covered, scheduled)

    # Soft warnings: preference missed, and leave booked on an existing weekly off.
    for (emp_id, day), brands in scheduled.items():
        if not brands:
            continue
        if day.weekday() in ctx.avoid[emp_id] or day in ctx.preferred_days[emp_id]:
            cited = sorted(brands, key=lambda bid: ctx.brands[bid].code)[0]
            add_conflict(
                severity="warning",
                conflict_type="preference",
                employee_id=emp_id,
                brand_id=cited,
                process_id=None,
                date=day,
                explanation=(
                    f"{_names(ctx, emp_id)} is scheduled on {day.isoformat()}, which they prefer to avoid. "
                    "Coverage required it, so the preference was not applied."
                ),
                suggestion="If someone else is authorised and free, swap this day. Otherwise leave the assignment.",
                suggestion_action=None,
            )

    for emp_id, days_off in ctx.leave_days.items():
        emp = ctx.employees.get(emp_id)
        if emp is None:
            continue
        for day in sorted(days_off):
            if day.weekday() not in ctx.weekly_offs[emp_id]:
                continue
            add_conflict(
                severity="warning",
                conflict_type="weekly_off_leave_conflict",
                employee_id=emp_id,
                brand_id=None,
                process_id=None,
                date=day,
                explanation=(
                    f"{emp.full_name}'s approved leave on {day.isoformat()} falls on their weekly off. "
                    "The day is blocked either way, but the leave does not add extra rest."
                ),
                suggestion="Move the leave onto a working day if the employee intended to extend their time off.",
                suggestion_action=None,
            )

    status_by_emp_day: dict[tuple[int, date], str] = {}
    brands_by_emp_day: dict[tuple[int, date], list[int]] = {}
    for emp_id in ctx.employees:
        for day in ctx.days:
            reason = block_reason(ctx, emp_id, day)
            brands = sorted(scheduled.get((emp_id, day), set()), key=lambda bid: ctx.brands[bid].code)
            if reason == "approved_leave":
                status = "approved_leave"
                brands = []
            elif reason == "comp_off":
                status = "comp_off"
                brands = []
            elif reason == "weekly_off":
                status = "weekly_off"
                brands = []
            elif reason in {"unavailable", "inactive"}:
                status = "unavailable"
                brands = []
            elif brands:
                status = "working"
            elif day in ctx.holidays:
                status = "public_holiday"
            elif _any_assignment_operates(ctx, emp_id, day):
                status = "available"
            else:
                status = "calendar_off"
            status_by_emp_day[(emp_id, day)] = status
            brands_by_emp_day[(emp_id, day)] = brands if status == "working" else []

    coverage_percent = round(100.0 * filled / demand, 1) if demand else 100.0
    blocking = [item for item in conflicts if item["severity"] in {"critical", "high"}]
    return SolveResult(
        year=year,
        month=month,
        days=ctx.days,
        status_by_emp_day=status_by_emp_day,
        brands_by_emp_day=brands_by_emp_day,
        holiday_dates=set(ctx.holidays),
        conflicts=conflicts,
        slots=slot_results,
        coverage_percent=coverage_percent,
        is_valid=len(blocking) == 0,
    )


def _any_assignment_operates(ctx: Context, emp_id: int, day: date) -> bool:
    for (employee_id, brand_id), processes in ctx.emp_brand_processes.items():
        if employee_id != emp_id:
            continue
        for process_id in processes:
            if rule_operates(ctx, brand_id, process_id, day):
                return True
    return False


def _record_gap(
    ctx: Context,
    conflicts: list[dict],
    day: date,
    brand_id: int,
    process_id: int,
    need: int,
    have: int,
    covered: dict,
    scheduled: dict,
) -> None:
    brand = ctx.brands[brand_id]
    process = ctx.processes[process_id]
    people = ctx.brand_process_emps.get((brand_id, process_id), [])
    reasons = []
    blocked_by_absence = False
    for emp_id, _primary in sorted(people, key=lambda item: ctx.employees[item[0]].employee_code):
        if emp_id in covered[(day, brand_id, process_id)]:
            continue
        reason = block_reason(ctx, emp_id, day)
        if reason:
            if reason in {"approved_leave", "comp_off", "unavailable"}:
                blocked_by_absence = True
            reasons.append(f"{_names(ctx, emp_id)} is on {BLOCK_LABELS.get(reason, reason)}")
            continue
        brands_today = scheduled[(emp_id, day)]
        if brand_id not in brands_today and len(brands_today) >= ctx.employees[emp_id].max_daily_workload:
            other = ", ".join(ctx.brands[bid].name for bid in sorted(brands_today))
            reasons.append(
                f"{_names(ctx, emp_id)} is already at the workload limit covering {other}"
            )
    if not people:
        reasons.append("no employee is authorised for this process")

    if have == 0 and not people:
        conflict_type = "no_available_employee"
        severity = "critical"
    elif have == 0 and blocked_by_absence:
        conflict_type = "availability_gap"
        severity = "critical"
    elif have == 0:
        conflict_type = "no_available_employee"
        severity = "critical"
    else:
        conflict_type = "insufficient_coverage"
        severity = "high"

    suggestion, action = _suggest(ctx, day, brand_id, process_id, scheduled)
    why = "; ".join(reasons) if reasons else "not enough authorised people were free"
    conflicts.append(
        {
            "severity": severity,
            "conflict_type": conflict_type,
            "employee_id": people[0][0] if len(people) == 1 else None,
            "brand_id": brand_id,
            "process_id": process_id,
            "date": day,
            "explanation": (
                f"{brand.name} / {process.name} on {day.strftime('%d %b %Y')} needs {need} "
                f"and has {have}. {why[0].upper() + why[1:]}."
            ),
            "suggestion": suggestion,
            "suggestion_action": action,
        }
    )


def _suggest(ctx: Context, day: date, brand_id: int, process_id: int, scheduled: dict) -> tuple[str, dict | None]:
    """Recommend a free colleague who could be authorised, preferring the brand's pod."""
    authorised = {emp_id for emp_id, _flag in ctx.brand_process_emps.get((brand_id, process_id), [])}
    brand = ctx.brands[brand_id]
    process = ctx.processes[process_id]
    candidates = []
    for emp in ctx.employees.values():
        if emp.id in authorised or emp.employment_status != "active":
            continue
        if block_reason(ctx, emp.id, day):
            continue
        used = len(scheduled[(emp.id, day)])
        spare = emp.max_daily_workload - used
        if spare <= 0:
            continue
        same_pod = 0 if emp.pod_id == brand.pod_id else 1
        knows_process = 1
        for (employee_id, _brand_id), procs in ctx.emp_brand_processes.items():
            if employee_id == emp.id and process_id in procs:
                knows_process = 0
                break
        candidates.append((same_pod, knows_process, -spare, emp.employee_code, emp))
    if not candidates:
        return (
            "No spare authorised or same-company employee has capacity. Add staffing, or lower the minimum for this day.",
            None,
        )
    candidates.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
    chosen = candidates[0][4]
    where = "in the same pod" if chosen.pod_id == brand.pod_id else "in another pod, with spare capacity"
    return (
        f"Authorise {chosen.full_name} ({chosen.employee_code}) for {process.name}. "
        f"They are {where} on {day.isoformat()} and can take {brand.name} without exceeding workload.",
        {
            "type": "authorize_and_assign",
            "employee_id": chosen.id,
            "brand_id": brand_id,
            "process_id": process_id,
            "date": day.isoformat(),
        },
    )


def _snapshot(ctx: Context, result: SolveResult) -> dict:
    per_brand: dict[int, dict] = {}
    for slot in result.slots:
        bucket = per_brand.setdefault(
            slot.brand_id,
            {"id": slot.brand_id, "name": ctx.brands[slot.brand_id].name, "met": 0, "total": 0},
        )
        bucket["total"] += 1
        if slot.have >= slot.need:
            bucket["met"] += 1
    brands = []
    for bucket in per_brand.values():
        bucket["coverage"] = round(100.0 * bucket["met"] / bucket["total"], 1) if bucket["total"] else 100.0
        brands.append(bucket)
    brands.sort(key=lambda item: (item["coverage"], item["name"]))

    mix: dict[str, int] = defaultdict(int)
    for status in result.status_by_emp_day.values():
        mix[status] += 1
    labels = {
        "working": "Working",
        "weekly_off": "Weekly off",
        "public_holiday": "Public holiday",
        "approved_leave": "Approved leave",
        "comp_off": "Comp-off",
        "calendar_off": "Calendar off",
        "available": "Available",
        "unavailable": "Unavailable",
    }
    status_mix = [{"name": labels.get(key, key), "key": key, "value": value} for key, value in sorted(mix.items())]
    critical = sum(1 for item in result.conflicts if item["severity"] == "critical")
    high = sum(1 for item in result.conflicts if item["severity"] == "high")
    warning = sum(1 for item in result.conflicts if item["severity"] == "warning")
    return {
        "brands": brands,
        "status_mix": status_mix,
        "critical": critical,
        "high": high,
        "warning": warning,
    }


def _assert_integrity(ctx: Context, result: SolveResult) -> None:
    for (emp_id, day), status in result.status_by_emp_day.items():
        brands = result.brands_by_emp_day[(emp_id, day)]
        if status == "working":
            reason = block_reason(ctx, emp_id, day)
            if reason:
                raise RuntimeError(f"Scheduled {emp_id} on {day} despite {reason}")
            limit = ctx.employees[emp_id].max_daily_workload
            if len(brands) > limit:
                raise RuntimeError(f"Workload exceeded for {emp_id} on {day}")
            for brand_id in brands:
                if not ctx.emp_brand_processes.get((emp_id, brand_id)):
                    raise RuntimeError(f"Unauthorised brand {brand_id} for {emp_id} on {day}")
        elif brands:
            raise RuntimeError(f"Non-working status {status} still has brands for {emp_id} on {day}")


def generate_roster(db: Session, year: int, month: int, hypo: Hypothetical | None = None, persist: bool = True) -> tuple[Roster | None, SolveResult]:
    result = solve(db, year, month, hypo)
    ctx = load_context(db, year, month, hypo)
    _assert_integrity(ctx, result)
    if not persist:
        return None, result

    roster = db.query(Roster).filter(Roster.year == year, Roster.month == month).one_or_none()
    if roster is None:
        roster = Roster(year=year, month=month)
        db.add(roster)
        db.flush()
    else:
        entry_ids = [row[0] for row in db.query(RosterEntry.id).filter(RosterEntry.roster_id == roster.id)]
        if entry_ids:
            db.query(RosterAssignment).filter(RosterAssignment.entry_id.in_(entry_ids)).delete(synchronize_session=False)
            db.query(RosterEntry).filter(RosterEntry.id.in_(entry_ids)).delete(synchronize_session=False)
        db.query(SchedulingConflict).filter(SchedulingConflict.roster_id == roster.id).delete(synchronize_session=False)
        db.flush()

    for emp_id in ctx.employees:
        for day in result.days:
            entry = RosterEntry(
                roster_id=roster.id,
                employee_id=emp_id,
                date=day,
                status=result.status_by_emp_day[(emp_id, day)],
                on_public_holiday=day in result.holiday_dates,
            )
            db.add(entry)
            db.flush()
            for brand_id in result.brands_by_emp_day[(emp_id, day)]:
                db.add(RosterAssignment(entry_id=entry.id, brand_id=brand_id))

    for item in result.conflicts:
        db.add(
            SchedulingConflict(
                roster_id=roster.id,
                severity=item["severity"],
                conflict_type=item["conflict_type"],
                employee_id=item.get("employee_id"),
                brand_id=item.get("brand_id"),
                process_id=item.get("process_id"),
                date=item.get("date"),
                explanation=item["explanation"],
                suggestion=item.get("suggestion") or "",
                suggestion_action=json.dumps(item["suggestion_action"]) if item.get("suggestion_action") else "",
                resolved=False,
            )
        )

    critical = sum(1 for item in result.conflicts if item["severity"] == "critical")
    high = sum(1 for item in result.conflicts if item["severity"] == "high")
    warning = sum(1 for item in result.conflicts if item["severity"] == "warning")
    roster.status = "valid" if result.is_valid else "partial"
    roster.is_valid = result.is_valid
    roster.coverage_percent = result.coverage_percent
    roster.conflict_count = critical + high
    roster.warning_count = warning
    roster.summary_json = json.dumps(_snapshot(ctx, result))
    roster.generated_at = utcnow()
    db.commit()
    db.refresh(roster)
    return roster, result


def regenerate_if_exists(db: Session, year: int, month: int) -> Roster | None:
    exists = db.query(Roster.id).filter(Roster.year == year, Roster.month == month).first()
    if not exists:
        return None
    roster, _result = generate_roster(db, year, month)
    return roster


def regenerate_overlapping(db: Session, start: date, end: date) -> None:
    cursor = date(start.year, start.month, 1)
    last = date(end.year, end.month, 1)
    while cursor <= last:
        regenerate_if_exists(db, cursor.year, cursor.month)
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)


def regenerate_all(db: Session) -> None:
    months = [(row.year, row.month) for row in db.query(Roster.year, Roster.month).all()]
    for year, month in months:
        generate_roster(db, year, month)

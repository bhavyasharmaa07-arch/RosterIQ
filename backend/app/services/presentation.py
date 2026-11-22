"""Presentation layer: builds RosterView and DashboardOut from relational data."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from typing import Any

from sqlalchemy.orm import Session, selectinload

from app.models import (
    AuditLog,
    Brand,
    CoverageRequirement,
    Employee,
    EmployeeAssignment,
    Leave,
    Pod,
    Process,
    PublicHoliday,
    Roster,
    RosterAssignment,
    RosterEntry,
    SchedulingConflict,
    WorkingRule,
)
from app.schemas import (
    AuditOut,
    CellOut,
    CoverageCell,
    CoverageRow,
    DashboardOut,
    HolidayOut,
    RosterRow,
    RosterSummary,
    RosterView,
)
from app.services.scheduler import month_days, rule_operates, min_staff, load_context


def build_roster_view(
    db: Session,
    year: int,
    month: int,
    view: str = "employee",
    pod_id: int | None = None,
    brand_id: int | None = None,
    search: str | None = None,
) -> RosterView:
    # Normalize query params if passed directly from FastAPI Query objects in tests
    clean_pod_id = pod_id if isinstance(pod_id, int) else None
    clean_brand_id = brand_id if isinstance(brand_id, int) else None
    clean_search = search.strip() if isinstance(search, str) and search.strip() else None

    days = month_days(year, month)
    holidays_db = db.query(PublicHoliday).filter(
        PublicHoliday.date >= days[0], PublicHoliday.date <= days[-1]
    ).all()
    holidays = [HolidayOut(id=h.id, date=h.date, name=h.name) for h in holidays_db]

    roster = db.query(Roster).filter(Roster.year == year, Roster.month == month).first()
    summary: RosterSummary | None = None
    if roster:
        summary = RosterSummary(
            id=roster.id,
            year=roster.year,
            month=roster.month,
            status=roster.status,
            is_valid=roster.is_valid,
            coverage_percent=roster.coverage_percent,
            conflict_count=roster.conflict_count,
            warning_count=roster.warning_count,
            generated_at=roster.generated_at,
        )

    roster_rows: list[RosterRow] = []
    coverage_rows: list[CoverageRow] = []

    if view == "employee" or not view:
        # Load employees
        query = db.query(Employee).options(selectinload(Employee.pod))
        if clean_pod_id:
            query = query.filter(Employee.pod_id == clean_pod_id)
        if clean_search:
            pattern = f"%{clean_search.lower()}%"
            query = query.filter(
                (Employee.full_name.ilike(pattern)) | (Employee.employee_code.ilike(pattern))
            )
        employees = query.order_by(Employee.pod_id, Employee.employee_code).all()

        # Load all entries for these employees if roster exists
        entries_by_emp_day: dict[tuple[int, date], RosterEntry] = {}
        if roster:
            entries = (
                db.query(RosterEntry)
                .filter(RosterEntry.roster_id == roster.id)
                .options(selectinload(RosterEntry.brands).selectinload(RosterAssignment.brand))
                .all()
            )
            for e in entries:
                entries_by_emp_day[(e.employee_id, e.date)] = e

        # Preload assignments to know employee processes per brand
        emp_assignments = (
            db.query(EmployeeAssignment)
            .options(selectinload(EmployeeAssignment.brand), selectinload(EmployeeAssignment.process))
            .all()
        )
        emp_brand_procs: dict[tuple[int, int], list[str]] = defaultdict(list)
        for ea in emp_assignments:
            emp_brand_procs[(ea.employee_id, ea.brand_id)].append(ea.process.code)

        # Preload conflicts for day gap indicators
        conflicts_by_emp_day: set[tuple[int, date]] = set()
        if roster:
            conf_query = db.query(SchedulingConflict.employee_id, SchedulingConflict.date).filter(
                SchedulingConflict.roster_id == roster.id,
                SchedulingConflict.employee_id.isnot(None),
                SchedulingConflict.date.isnot(None),
                SchedulingConflict.severity.in_(["critical", "high"]),
            ).all()
            for emp_ref, day_ref in conf_query:
                conflicts_by_emp_day.add((emp_ref, day_ref))

        for emp in employees:
            cells: list[CellOut] = []
            for d in days:
                entry = entries_by_emp_day.get((emp.id, d))
                status = entry.status if entry else "available"
                on_holiday = entry.on_public_holiday if entry else (d in {h.date for h in holidays})
                assigned_brands: list[str] = []
                assigned_brand_ids: list[int] = []
                assigned_processes: list[str] = []
                if entry and entry.brands:
                    for ra in entry.brands:
                        assigned_brands.append(ra.brand.name)
                        assigned_brand_ids.append(ra.brand.id)
                        procs = emp_brand_procs.get((emp.id, ra.brand_id), [])
                        assigned_processes.extend(procs)

                cells.append(
                    CellOut(
                        date=d,
                        status=status,
                        brands=assigned_brands,
                        processes=sorted(set(assigned_processes)),
                        brand_ids=assigned_brand_ids,
                        on_public_holiday=on_holiday,
                        has_gap=(emp.id, d) in conflicts_by_emp_day,
                    )
                )

            roster_rows.append(
                RosterRow(
                    employee_id=emp.id,
                    employee_code=emp.employee_code,
                    full_name=emp.full_name,
                    pod_id=emp.pod_id,
                    pod_name=emp.pod.name if emp.pod else "",
                    is_pod_lead=emp.pod and emp.pod.lead_id == emp.id,
                    designation=emp.designation,
                    cells=cells,
                )
            )

    elif view == "coverage":
        # Brand-process coverage matrix
        ctx = load_context(db, year, month)
        rules = db.query(WorkingRule).options(
            selectinload(WorkingRule.brand).selectinload(Brand.pod),
            selectinload(WorkingRule.process),
        ).all()

        # If roster exists, map which employees are working on which brand each day
        working_by_brand_day: dict[tuple[int, date], set[int]] = defaultdict(set)
        if roster:
            entries = (
                db.query(RosterEntry)
                .filter(RosterEntry.roster_id == roster.id, RosterEntry.status == "working")
                .options(selectinload(RosterEntry.brands))
                .all()
            )
            for e in entries:
                for ra in e.brands:
                    working_by_brand_day[(ra.brand_id, e.date)].add(e.employee_id)

        for r in rules:
            if clean_pod_id and r.brand.pod_id != clean_pod_id:
                continue
            if clean_brand_id and r.brand_id != clean_brand_id:
                continue
            if clean_search:
                pattern = clean_search.lower()
                if (
                    pattern not in r.brand.name.lower()
                    and pattern not in r.brand.code.lower()
                    and pattern not in r.process.name.lower()
                ):
                    continue

            cells: list[CoverageCell] = []
            authorised_emps = [
                emp_id for emp_id, _ in ctx.brand_process_emps.get((r.brand_id, r.process_id), [])
            ]

            for d in days:
                operates = rule_operates(ctx, r.brand_id, r.process_id, d)
                if not operates:
                    cells.append(
                        CoverageCell(
                            date=d,
                            state="closed",
                            required=0,
                            assigned=0,
                            employees=[],
                        )
                    )
                    continue

                needed = min_staff(ctx, r.brand_id, r.process_id, d)
                working_emps = working_by_brand_day.get((r.brand_id, d), set())
                active_assigned = [
                    ctx.employees[eid].full_name
                    for eid in authorised_emps
                    if eid in working_emps
                ]
                assigned_count = len(active_assigned)
                state = "covered" if assigned_count >= needed else ("gap" if needed > 0 else "covered")

                cells.append(
                    CoverageCell(
                        date=d,
                        state=state,
                        required=needed,
                        assigned=assigned_count,
                        employees=active_assigned,
                    )
                )

            coverage_rows.append(
                CoverageRow(
                    brand_id=r.brand_id,
                    brand_name=r.brand.name,
                    process_id=r.process_id,
                    process_name=r.process.name,
                    process_code=r.process.code,
                    cells=cells,
                )
            )

        coverage_rows.sort(key=lambda x: (x.brand_name, x.process_name))

    return RosterView(
        roster=summary,
        year=year,
        month=month,
        days=days,
        holidays=holidays,
        rows=roster_rows,
        coverage_rows=coverage_rows,
        view=view,
    )


def build_dashboard(db: Session, year: int, month: int) -> DashboardOut:
    days = month_days(year, month)
    start_date, end_date = days[0], days[-1]

    total_employees = db.query(Employee).count()
    active_employees = db.query(Employee).filter(Employee.employment_status == "active").count()
    total_brands = db.query(Brand).count()
    total_pods = db.query(Pod).count()
    total_processes = db.query(Process).count()

    roster = db.query(Roster).filter(Roster.year == year, Roster.month == month).first()

    # Leaves during this month
    leaves = (
        db.query(Leave)
        .filter(
            Leave.status == "approved",
            Leave.start_date <= end_date,
            Leave.end_date >= start_date,
        )
        .options(selectinload(Leave.employee).selectinload(Employee.pod))
        .all()
    )

    on_leave_data = [
        {
            "id": lv.id,
            "employee_id": lv.employee_id,
            "employee_name": lv.employee.full_name,
            "employee_code": lv.employee.employee_code,
            "pod_name": lv.employee.pod.name if lv.employee.pod else "",
            "start_date": lv.start_date.isoformat(),
            "end_date": lv.end_date.isoformat(),
            "leave_type": lv.leave_type,
            "reason": lv.reason,
        }
        for lv in leaves
    ]

    # Upcoming weekly offs (sample distribution of days of week)
    employees = db.query(Employee).options(selectinload(Employee.pod)).all()
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekly_off_counts = defaultdict(int)
    for emp in employees:
        weekly_off_counts[emp.weekly_off_preference] += 1

    upcoming_offs = [
        {"day_number": dow, "day_name": day_names[dow], "employee_count": count}
        for dow, count in sorted(weekly_off_counts.items())
    ]

    # Audit logs
    recent_logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(10)
        .all()
    )
    audit_out = [
        AuditOut(
            id=log.id,
            created_at=log.created_at,
            action=log.action,
            entity=log.entity,
            detail=log.detail,
        )
        for log in recent_logs
    ]

    # Parse roster summary JSON if available
    brand_coverage: list[dict[str, Any]] = []
    status_mix: list[dict[str, Any]] = []
    if roster and roster.summary_json:
        try:
            snapshot = json.loads(roster.summary_json)
            brand_coverage = snapshot.get("brands", [])
            status_mix = snapshot.get("status_mix", [])
        except Exception:
            pass

    return DashboardOut(
        year=year,
        month=month,
        total_employees=total_employees,
        active_employees=active_employees,
        total_brands=total_brands,
        total_pods=total_pods,
        total_processes=total_processes,
        roster_status=roster.status if roster else "not_generated",
        is_valid=roster.is_valid if roster else False,
        coverage_percent=roster.coverage_percent if roster else 0.0,
        unresolved_conflicts=roster.conflict_count if roster else 0,
        warning_count=roster.warning_count if roster else 0,
        employees_on_leave=len(on_leave_data),
        on_leave=on_leave_data,
        upcoming_weekly_offs=upcoming_offs,
        brand_coverage=brand_coverage,
        status_mix=status_mix,
        recent_changes=audit_out,
    )

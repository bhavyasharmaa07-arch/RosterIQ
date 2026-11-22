"""Excel export service: generates a multi-sheet styled workbook for RosterIQ."""

from __future__ import annotations

import io
from datetime import date
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from sqlalchemy.orm import Session, selectinload

from app.models import Employee, Roster, RosterEntry, RosterAssignment, SchedulingConflict, WorkingRule, Brand, Process
from app.services.scheduler import month_days, rule_operates, min_staff, load_context


def generate_roster_excel(db: Session, year: int, month: int) -> io.BytesIO:
    wb = openpyxl.Workbook()
    # Sheet 1: Employee Schedule
    ws_emp = wb.active
    ws_emp.title = "Employee Schedule"

    days = month_days(year, month)
    roster = db.query(Roster).filter(Roster.year == year, Roster.month == month).first()

    # Styles
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    fill_header = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")  # Dark Blue
    font_sub = Font(name="Calibri", size=10, bold=True)
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    border_thin = Border(
        left=Side(style="thin", color="D1D5DB"),
        right=Side(style="thin", color="D1D5DB"),
        top=Side(style="thin", color="D1D5DB"),
        bottom=Side(style="thin", color="D1D5DB"),
    )

    # Status fills
    fills = {
        "working": PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid"),  # light green
        "weekly_off": PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid"),  # light gray
        "approved_leave": PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid"),  # light amber
        "comp_off": PatternFill(start_color="E0E7FF", end_color="E0E7FF", fill_type="solid"),  # light indigo
        "public_holiday": PatternFill(start_color="F3E8FF", end_color="F3E8FF", fill_type="solid"),  # light purple
        "unavailable": PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid"),  # light red
        "available": PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid"),
        "calendar_off": PatternFill(start_color="F9FAFB", end_color="F9FAFB", fill_type="solid"),
    }

    # Headers for Sheet 1
    headers = ["Emp Code", "Full Name", "Pod", "Designation", "Workload"] + [f"{d.day:02d}-{d.strftime('%a')}" for d in days] + ["Total Work", "Total Off"]
    for col_idx, h in enumerate(headers, start=1):
        cell = ws_emp.cell(row=1, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center

    employees = db.query(Employee).options(selectinload(Employee.pod)).order_by(Employee.pod_id, Employee.employee_code).all()
    entries_map: dict[tuple[int, date], RosterEntry] = {}
    if roster:
        entries = db.query(RosterEntry).filter(RosterEntry.roster_id == roster.id).options(
            selectinload(RosterEntry.brands).selectinload(RosterAssignment.brand)
        ).all()
        for e in entries:
            entries_map[(e.employee_id, e.date)] = e

    row_idx = 2
    for emp in employees:
        ws_emp.cell(row=row_idx, column=1, value=emp.employee_code).alignment = align_left
        ws_emp.cell(row=row_idx, column=2, value=emp.full_name).alignment = align_left
        ws_emp.cell(row=row_idx, column=3, value=emp.pod.name if emp.pod else "").alignment = align_left
        ws_emp.cell(row=row_idx, column=4, value=emp.designation).alignment = align_left
        ws_emp.cell(row=row_idx, column=5, value=emp.max_daily_workload).alignment = align_center

        total_work = 0
        total_off = 0
        for col_offset, d in enumerate(days, start=6):
            entry = entries_map.get((emp.id, d))
            status = entry.status if entry else "available"
            brands = [ra.brand.name for ra in entry.brands] if entry and entry.brands else []

            val = status.replace("_", " ").title()
            if status == "working" and brands:
                val = f"Work: {', '.join(brands)}"
                total_work += 1
            elif status in {"weekly_off", "calendar_off", "public_holiday"}:
                total_off += 1

            cell = ws_emp.cell(row=row_idx, column=col_offset, value=val)
            cell.alignment = align_center
            cell.border = border_thin
            if status in fills:
                cell.fill = fills[status]

        ws_emp.cell(row=row_idx, column=len(headers) - 1, value=total_work).alignment = align_center
        ws_emp.cell(row=row_idx, column=len(headers), value=total_off).alignment = align_center
        row_idx += 1

    # Sheet 2: Brand Coverage
    ws_cov = wb.create_sheet(title="Brand Coverage")
    cov_headers = ["Pod", "Brand", "Process", "Rule", "Min Staff"] + [f"{d.day:02d}-{d.strftime('%a')}" for d in days]
    for col_idx, h in enumerate(cov_headers, start=1):
        cell = ws_cov.cell(row=1, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center

    ctx = load_context(db, year, month)
    rules = db.query(WorkingRule).options(
        selectinload(WorkingRule.brand).selectinload(Brand.pod),
        selectinload(WorkingRule.process),
    ).all()

    working_by_brand_day = {}
    if roster:
        working_entries = db.query(RosterEntry).filter(RosterEntry.roster_id == roster.id, RosterEntry.status == "working").options(selectinload(RosterEntry.brands)).all()
        for we in working_entries:
            for ra in we.brands:
                working_by_brand_day.setdefault((ra.brand_id, we.date), set()).add(we.employee_id)

    fill_gap = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    fill_covered = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
    fill_closed = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")

    row_idx = 2
    for r in sorted(rules, key=lambda x: (x.brand.pod.name if x.brand.pod else "", x.brand.name, x.process.name)):
        ws_cov.cell(row=row_idx, column=1, value=r.brand.pod.name if r.brand.pod else "").alignment = align_left
        ws_cov.cell(row=row_idx, column=2, value=r.brand.name).alignment = align_left
        ws_cov.cell(row=row_idx, column=3, value=r.process.name).alignment = align_left
        ws_cov.cell(row=row_idx, column=4, value=r.mode).alignment = align_center
        ws_cov.cell(row=row_idx, column=5, value=1).alignment = align_center

        authorised_emps = [emp_id for emp_id, _ in ctx.brand_process_emps.get((r.brand_id, r.process_id), [])]

        for col_offset, d in enumerate(days, start=6):
            operates = rule_operates(ctx, r.brand_id, r.process_id, d)
            if not operates:
                c = ws_cov.cell(row=row_idx, column=col_offset, value="Closed")
                c.fill = fill_closed
            else:
                needed = min_staff(ctx, r.brand_id, r.process_id, d)
                working_emps = working_by_brand_day.get((r.brand_id, d), set())
                assigned = sum(1 for eid in authorised_emps if eid in working_emps)
                c = ws_cov.cell(row=row_idx, column=col_offset, value=f"{assigned}/{needed}")
                c.fill = fill_covered if assigned >= needed else fill_gap
            c.alignment = align_center
            c.border = border_thin
        row_idx += 1

    # Sheet 3: Conflicts
    ws_conf = wb.create_sheet(title="Conflicts & Gaps")
    conf_headers = ["Severity", "Date", "Brand", "Process", "Employee", "Conflict Type", "Explanation", "Suggestion"]
    for col_idx, h in enumerate(conf_headers, start=1):
        cell = ws_conf.cell(row=1, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center

    if roster:
        conflicts = db.query(SchedulingConflict).filter(SchedulingConflict.roster_id == roster.id).order_by(SchedulingConflict.severity, SchedulingConflict.date).all()
        for idx, cf in enumerate(conflicts, start=2):
            brand = db.query(Brand).filter(Brand.id == cf.brand_id).first() if cf.brand_id else None
            proc = db.query(Process).filter(Process.id == cf.process_id).first() if cf.process_id else None
            emp = db.query(Employee).filter(Employee.id == cf.employee_id).first() if cf.employee_id else None

            ws_conf.cell(row=idx, column=1, value=cf.severity.upper()).alignment = align_center
            ws_conf.cell(row=idx, column=2, value=cf.date.isoformat() if cf.date else "").alignment = align_center
            ws_conf.cell(row=idx, column=3, value=brand.name if brand else "").alignment = align_left
            ws_conf.cell(row=idx, column=4, value=proc.name if proc else "").alignment = align_left
            ws_conf.cell(row=idx, column=5, value=emp.full_name if emp else "").alignment = align_left
            ws_conf.cell(row=idx, column=6, value=cf.conflict_type).alignment = align_left
            ws_conf.cell(row=idx, column=7, value=cf.explanation).alignment = align_left
            ws_conf.cell(row=idx, column=8, value=cf.suggestion).alignment = align_left

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

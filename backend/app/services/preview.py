"""What-if preview service: predicts the impact of a day edit before persisting."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Employee, Brand, Process, Roster, SchedulingConflict
from app.schemas import DayEditIn, PreviewOut, ConflictOut
from app.services.scheduler import Hypothetical, solve


def preview_day_edit(db: Session, year: int, month: int, edit: DayEditIn) -> PreviewOut:
    hypo = Hypothetical()

    if edit.status == "working":
        hypo.extra_overrides[(edit.employee_id, edit.date)] = ("working", edit.brand_ids)
        if edit.authorise:
            # Grant hypothetical authorization for the selected brands and all their processes
            for bid in edit.brand_ids:
                procs = db.query(Process).all()
                for p in procs:
                    hypo.extra_assignments.append((edit.employee_id, bid, p.id, True))
    else:
        hypo.extra_overrides[(edit.employee_id, edit.date)] = (edit.status, [])

    # Solve in-memory
    result = solve(db, year, month, hypo=hypo)

    # Load baseline roster conflicts to calculate difference
    baseline_roster = db.query(Roster).filter(Roster.year == year, Roster.month == month).first()
    baseline_count = baseline_roster.conflict_count if baseline_roster else 0

    new_blocking_conflicts = [c for c in result.conflicts if c["severity"] in {"critical", "high"}]
    total_new_blocking = len(new_blocking_conflicts)
    resolved_count = max(0, baseline_count - total_new_blocking)

    emp = db.query(Employee).filter(Employee.id == edit.employee_id).first()
    emp_name = emp.full_name if emp else f"Employee #{edit.employee_id}"

    status_label = edit.status.replace("_", " ").title()
    summary = (
        f"Setting {emp_name} to '{status_label}' on {edit.date.strftime('%d %b %Y')} yields "
        f"{result.coverage_percent}% coverage. "
    )
    if result.is_valid:
        summary += "The proposed schedule is fully compliant with all constraints."
    elif total_new_blocking > baseline_count:
        summary += f"WARNING: This change increases unresolved conflicts by {total_new_blocking - baseline_count}."
    else:
        summary += f"This change resolves {resolved_count} conflict(s)."

    conflict_outs: list[ConflictOut] = []
    for idx, c in enumerate(result.conflicts):
        bid = c.get("brand_id")
        pid = c.get("process_id")
        eid = c.get("employee_id")
        brand = db.query(Brand).filter(Brand.id == bid).first() if bid else None
        proc = db.query(Process).filter(Process.id == pid).first() if pid else None
        employee = db.query(Employee).filter(Employee.id == eid).first() if eid else None

        conflict_outs.append(
            ConflictOut(
                id=idx + 1,
                severity=c["severity"],
                conflict_type=c["conflict_type"],
                employee_id=eid,
                employee_name=employee.full_name if employee else None,
                employee_code=employee.employee_code if employee else None,
                brand_id=bid,
                brand_name=brand.name if brand else None,
                process_id=pid,
                process_name=proc.name if proc else None,
                date=c.get("date"),
                explanation=c["explanation"],
                suggestion=c.get("suggestion") or "",
                suggestion_action=c.get("suggestion_action"),
            )
        )

    requires_confirmation = (not result.is_valid) or (total_new_blocking > baseline_count)

    return PreviewOut(
        summary=summary,
        requires_confirmation=requires_confirmation,
        is_valid=result.is_valid,
        coverage_percent=result.coverage_percent,
        new_conflicts=conflict_outs[:20],  # top 20 representative conflicts
        resolved_count=resolved_count,
    )

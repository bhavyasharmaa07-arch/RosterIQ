"""Conflicts API router."""

import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog, Brand, Employee, EmployeeAssignment, Process, Roster, SchedulingConflict
from app.schemas import ConflictOut
from app.services.scheduler import generate_roster

router = APIRouter(prefix="/conflicts", tags=["Conflicts"])


@router.get("", response_model=list[ConflictOut])
def list_conflicts(
    year: int = Query(default=2026, ge=2024, le=2100),
    month: int = Query(default=11, ge=1, le=12),
    severity: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ConflictOut]:
    roster = db.query(Roster).filter(Roster.year == year, Roster.month == month).first()
    if not roster:
        return []

    clean_severity = severity.lower() if isinstance(severity, str) and severity.strip() else None
    query = db.query(SchedulingConflict).filter(SchedulingConflict.roster_id == roster.id)
    if clean_severity:
        query = query.filter(SchedulingConflict.severity == clean_severity)

    conflicts = query.order_by(
        SchedulingConflict.severity,
        SchedulingConflict.date,
        SchedulingConflict.id,
    ).all()

    output = []
    for c in conflicts:
        brand = db.query(Brand).filter(Brand.id == c.brand_id).first() if c.brand_id else None
        proc = db.query(Process).filter(Process.id == c.process_id).first() if c.process_id else None
        emp = db.query(Employee).filter(Employee.id == c.employee_id).first() if c.employee_id else None

        action_dict = None
        if c.suggestion_action:
            try:
                action_dict = json.loads(c.suggestion_action)
            except Exception:
                pass

        output.append(
            ConflictOut(
                id=c.id,
                severity=c.severity,
                conflict_type=c.conflict_type,
                employee_id=c.employee_id,
                employee_name=emp.full_name if emp else None,
                employee_code=emp.employee_code if emp else None,
                brand_id=c.brand_id,
                brand_name=brand.name if brand else None,
                process_id=c.process_id,
                process_name=proc.name if proc else None,
                date=c.date,
                explanation=c.explanation,
                suggestion=c.suggestion,
                suggestion_action=action_dict,
            )
        )
    return output


@router.post("/{conflict_id}/resolve")
def resolve_conflict(conflict_id: int, db: Session = Depends(get_db)):
    conflict = db.query(SchedulingConflict).filter(SchedulingConflict.id == conflict_id).first()
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")

    if not conflict.suggestion_action:
        raise HTTPException(status_code=400, detail="No actionable suggestion available for this conflict")

    try:
        action = json.loads(conflict.suggestion_action)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid suggestion action payload")

    action_type = action.get("type")
    if action_type == "authorize_and_assign":
        emp_id = action.get("employee_id")
        brand_id = action.get("brand_id")
        process_id = action.get("process_id")

        existing = db.query(EmployeeAssignment).filter(
            EmployeeAssignment.employee_id == emp_id,
            EmployeeAssignment.brand_id == brand_id,
            EmployeeAssignment.process_id == process_id,
        ).first()

        if not existing:
            db.add(
                EmployeeAssignment(
                    employee_id=emp_id,
                    brand_id=brand_id,
                    process_id=process_id,
                    is_primary=False,
                )
            )

        conflict.resolved = True
        db.add(
            AuditLog(
                action="resolve_conflict",
                entity="conflict",
                detail=f"Resolved conflict #{conflict_id}: Authorised employee #{emp_id} on brand #{brand_id}, process #{process_id}.",
            )
        )
        db.commit()

        # Regenerate roster for this conflict's month
        roster = db.query(Roster).filter(Roster.id == conflict.roster_id).first()
        if roster:
            generate_roster(db, roster.year, roster.month)

        return {"success": True, "message": "Authorisation granted and roster re-solved."}

    raise HTTPException(status_code=400, detail=f"Unsupported action type: {action_type}")

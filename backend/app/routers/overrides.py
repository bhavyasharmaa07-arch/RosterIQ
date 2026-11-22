"""Manager Overrides API router."""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog, Employee, RosterOverride
from app.schemas import DayEditIn, PreviewOut
from app.services.preview import preview_day_edit
from app.services.scheduler import generate_roster

router = APIRouter(prefix="/overrides", tags=["Overrides"])


@router.post("/preview", response_model=PreviewOut)
def preview_override_change(
    payload: DayEditIn,
    year: int = Query(default=2026, ge=2024, le=2100),
    month: int = Query(default=11, ge=1, le=12),
    db: Session = Depends(get_db),
) -> PreviewOut:
    return preview_day_edit(db, year, month, payload)


@router.post("")
def save_override(
    payload: DayEditIn,
    db: Session = Depends(get_db),
):
    emp = db.query(Employee).filter(Employee.id == payload.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    brand_ids_str = ",".join(str(b) for b in payload.brand_ids) if payload.status == "working" else ""

    override = db.query(RosterOverride).filter(
        RosterOverride.employee_id == payload.employee_id,
        RosterOverride.date == payload.date,
    ).first()

    if override:
        override.status = payload.status
        override.brand_ids = brand_ids_str
        override.note = payload.note
    else:
        override = RosterOverride(
            employee_id=payload.employee_id,
            date=payload.date,
            status=payload.status,
            brand_ids=brand_ids_str,
            note=payload.note,
        )
        db.add(override)

    db.add(
        AuditLog(
            action="set_override",
            entity="override",
            detail=f"Manager pin for {emp.full_name} on {payload.date.isoformat()}: status={payload.status}.",
        )
    )
    db.commit()

    # Re-solve the month
    generate_roster(db, payload.date.year, payload.date.month)
    return {"success": True, "message": "Override saved and roster updated."}


@router.delete("/{employee_id}/{target_date}")
def delete_override(
    employee_id: int,
    target_date: date,
    db: Session = Depends(get_db),
):
    override = db.query(RosterOverride).filter(
        RosterOverride.employee_id == employee_id,
        RosterOverride.date == target_date,
    ).first()

    if not override:
        raise HTTPException(status_code=404, detail="Override not found")

    db.delete(override)
    db.add(
        AuditLog(
            action="remove_override",
            entity="override",
            detail=f"Removed manager override for employee #{employee_id} on {target_date.isoformat()}.",
        )
    )
    db.commit()

    generate_roster(db, target_date.year, target_date.month)
    return {"success": True, "message": "Override removed and roster updated."}

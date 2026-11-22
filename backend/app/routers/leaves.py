"""Leaves and Comp-Offs API router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import AuditLog, CompOff, Employee, Leave
from app.schemas import CompOffIn, CompOffOut, LeaveIn, LeaveOut
from app.services.scheduler import regenerate_overlapping

leaves_router = APIRouter(prefix="/leaves", tags=["Leaves"])
compoffs_router = APIRouter(prefix="/comp-offs", tags=["Comp-Offs"])


@leaves_router.get("", response_model=list[LeaveOut])
def list_leaves(db: Session = Depends(get_db)) -> list[LeaveOut]:
    leaves = (
        db.query(Leave)
        .options(selectinload(Leave.employee))
        .order_by(Leave.start_date.desc())
        .all()
    )
    return [
        LeaveOut(
            id=lv.id,
            employee_id=lv.employee_id,
            employee_code=lv.employee.employee_code,
            employee_name=lv.employee.full_name,
            start_date=lv.start_date,
            end_date=lv.end_date,
            leave_type=lv.leave_type,
            status=lv.status,
            reason=lv.reason,
        )
        for lv in leaves
    ]


@leaves_router.post("", response_model=LeaveOut)
def create_leave(payload: LeaveIn, db: Session = Depends(get_db)) -> LeaveOut:
    emp = db.query(Employee).filter(Employee.id == payload.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    leave = Leave(
        employee_id=payload.employee_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        leave_type=payload.leave_type,
        status=payload.status,
        reason=payload.reason,
    )
    db.add(leave)
    db.add(
        AuditLog(
            action="request_leave",
            entity="leave",
            detail=f"Leave request ({payload.leave_type}) for {emp.full_name} from {payload.start_date} to {payload.end_date}: status={payload.status}.",
        )
    )
    db.commit()
    db.refresh(leave)

    if leave.status == "approved":
        regenerate_overlapping(db, leave.start_date, leave.end_date)

    return LeaveOut(
        id=leave.id,
        employee_id=leave.employee_id,
        employee_code=emp.employee_code,
        employee_name=emp.full_name,
        start_date=leave.start_date,
        end_date=leave.end_date,
        leave_type=leave.leave_type,
        status=leave.status,
        reason=leave.reason,
    )


@leaves_router.patch("/{leave_id}/status")
def update_leave_status(leave_id: int, status: str, db: Session = Depends(get_db)):
    if status not in {"pending", "approved", "rejected"}:
        raise HTTPException(status_code=400, detail="Invalid status")

    leave = db.query(Leave).options(selectinload(Leave.employee)).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")

    old_status = leave.status
    leave.status = status
    db.add(
        AuditLog(
            action="update_leave_status",
            entity="leave",
            detail=f"Updated leave #{leave.id} for {leave.employee.full_name} from {old_status} to {status}.",
        )
    )
    db.commit()

    # Regenerate rosters affected by this date range
    regenerate_overlapping(db, leave.start_date, leave.end_date)
    return {"success": True, "status": status, "message": f"Leave status updated to {status}."}


@compoffs_router.get("", response_model=list[CompOffOut])
def list_compoffs(db: Session = Depends(get_db)) -> list[CompOffOut]:
    items = (
        db.query(CompOff)
        .options(selectinload(CompOff.employee))
        .order_by(CompOff.off_date.desc())
        .all()
    )
    return [
        CompOffOut(
            id=c.id,
            employee_id=c.employee_id,
            employee_code=c.employee.employee_code,
            employee_name=c.employee.full_name,
            off_date=c.off_date,
            worked_date=c.worked_date,
            status=c.status,
            reason=c.reason,
        )
        for c in items
    ]

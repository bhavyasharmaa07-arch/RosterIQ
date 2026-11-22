"""Audit Logs API router."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog
from app.schemas import AuditOut

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("", response_model=list[AuditOut])
def list_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[AuditOut]:
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        AuditOut(
            id=log.id,
            created_at=log.created_at,
            action=log.action,
            entity=log.entity,
            detail=log.detail,
        )
        for log in logs
    ]

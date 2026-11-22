"""Roster API router."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog, Roster
from app.schemas import GenerateIn, RosterSummary, RosterView
from app.services.export import generate_roster_excel
from app.services.presentation import build_roster_view
from app.services.scheduler import generate_roster

router = APIRouter(prefix="/roster", tags=["Roster"])


@router.get("", response_model=RosterView)
def get_roster(
    year: int = Query(default=2026, ge=2024, le=2100),
    month: int = Query(default=11, ge=1, le=12),
    view: str = Query(default="employee"),
    pod_id: int | None = Query(default=None),
    brand_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> RosterView:
    return build_roster_view(
        db,
        year=year,
        month=month,
        view=view,
        pod_id=pod_id,
        brand_id=brand_id,
        search=search,
    )


@router.post("/generate", response_model=RosterSummary)
def trigger_generation(
    payload: GenerateIn,
    db: Session = Depends(get_db),
) -> RosterSummary:
    roster, result = generate_roster(db, payload.year, payload.month)
    if not roster:
        raise HTTPException(status_code=500, detail="Failed to persist roster")

    db.add(
        AuditLog(
            action="generate_roster",
            entity="roster",
            detail=f"Generated roster for {payload.month:02d}/{payload.year}: status {roster.status}, coverage {roster.coverage_percent}%.",
        )
    )
    db.commit()

    return RosterSummary(
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


@router.get("/export")
def export_roster_excel(
    year: int = Query(default=2026, ge=2024, le=2100),
    month: int = Query(default=11, ge=1, le=12),
    db: Session = Depends(get_db),
):
    buf = generate_roster_excel(db, year, month)
    filename = f"RosterIQ_{year}_{month:02d}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

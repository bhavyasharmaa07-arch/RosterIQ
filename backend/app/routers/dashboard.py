"""Dashboard API router."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DashboardOut
from app.services.presentation import build_dashboard

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardOut)
def get_dashboard_data(
    year: int = Query(default=2026, ge=2024, le=2100),
    month: int = Query(default=11, ge=1, le=12),
    db: Session = Depends(get_db),
) -> DashboardOut:
    return build_dashboard(db, year, month)

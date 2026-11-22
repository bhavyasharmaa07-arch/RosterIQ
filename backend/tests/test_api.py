"""Unit and integration tests for RosterIQ router functions."""

from datetime import date
import pytest
from app.database import SessionLocal, init_db
from app.schemas import DayEditIn, GenerateIn
from app.seed import seed_if_empty
from app.routers.dashboard import get_dashboard_data
from app.routers.roster import get_roster, trigger_generation, export_roster_excel
from app.routers.conflicts import list_conflicts, resolve_conflict
from app.routers.overrides import preview_override_change, save_override
from app.routers.employees import list_employees, get_employee
from app.routers.pods import list_pods, list_brands, list_processes
from app.routers.leaves import list_leaves, list_compoffs


@pytest.fixture(scope="module")
def db():
    init_db()
    seed_if_empty()
    session = SessionLocal()
    yield session
    session.close()


def test_dashboard_router(db):
    data = get_dashboard_data(year=2026, month=11, db=db)
    assert data.total_employees >= 30
    assert data.total_pods == 4
    assert data.total_brands == 24
    assert data.coverage_percent > 80.0
    assert len(data.brand_coverage) > 0


def test_roster_employee_view(db):
    view = get_roster(year=2026, month=11, view="employee", db=db)
    assert len(view.rows) >= 30
    assert len(view.days) == 30
    assert view.roster is not None
    assert view.roster.coverage_percent > 80.0


def test_roster_coverage_view(db):
    view = get_roster(year=2026, month=11, view="coverage", db=db)
    assert len(view.coverage_rows) > 0
    first_row = view.coverage_rows[0]
    assert len(first_row.cells) == 30


def test_list_conflicts(db):
    conflicts = list_conflicts(year=2026, month=11, db=db)
    assert len(conflicts) > 0
    assert any(c.severity == "critical" for c in conflicts)


def test_list_employees_and_pods(db):
    emps = list_employees(db=db)
    assert len(emps) >= 30
    pods = list_pods(db=db)
    assert len(pods) == 4
    brands = list_brands(db=db)
    assert len(brands) == 24
    procs = list_processes(db=db)
    assert len(procs) == 6


def test_whatif_preview(db):
    payload = DayEditIn(
        employee_id=1,
        date=date(2026, 11, 15),
        status="weekly_off",
        brand_ids=[],
        note="Testing what-if impact",
        authorise=False,
    )
    preview = preview_override_change(payload=payload, year=2026, month=11, db=db)
    assert preview.coverage_percent > 0
    assert len(preview.summary) > 0


def test_excel_export_response(db):
    from app.services.export import generate_roster_excel
    buf = generate_roster_excel(db, 2026, 11)
    assert len(buf.getvalue()) > 1000

    stream = export_roster_excel(year=2026, month=11, db=db)
    assert stream.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

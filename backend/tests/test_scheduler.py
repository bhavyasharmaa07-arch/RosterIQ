"""Unit tests for the scheduling engine and constraint solver."""

from datetime import date
import pytest
from app.database import SessionLocal, init_db
from app.seed import seed_if_empty
from app.services.scheduler import generate_roster, solve, block_reason, load_context


@pytest.fixture(scope="module")
def db():
    init_db()
    seed_if_empty()
    session = SessionLocal()
    yield session
    session.close()


def test_solve_november_2026(db):
    result = solve(db, 2026, 11)
    assert len(result.days) == 30
    assert result.coverage_percent > 85.0
    # Because EMP019 (Aisha Khan) is on notice and leaves are deliberately seeded, conflicts exist
    assert len(result.conflicts) > 0


def test_hard_constraint_blocking(db):
    ctx = load_context(db, 2026, 11)
    # EMP022 has approved leave on 2026-11-22 and 2026-11-23
    reason_22 = block_reason(ctx, 22, date(2026, 11, 22))
    assert reason_22 in {"approved_leave", "weekly_off"}

    # EMP019 is on notice -> blocked as inactive
    reason_19 = block_reason(ctx, 19, date(2026, 11, 10))
    assert reason_19 == "inactive"


def test_generate_roster_persistence(db):
    roster, result = generate_roster(db, 2026, 11)
    assert roster is not None
    assert roster.year == 2026
    assert roster.month == 11
    assert roster.coverage_percent == result.coverage_percent
    assert roster.status in {"valid", "partial"}

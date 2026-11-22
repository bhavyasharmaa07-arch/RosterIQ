"""Unit tests for RosterIQ database models and seed setup."""

import pytest
from app.database import SessionLocal, init_db
from app.models import Employee, Pod, Brand, Process, Roster, PublicHoliday
from app.seed import seed_if_empty


@pytest.fixture(scope="module")
def db_session():
    init_db()
    seed_if_empty()
    db = SessionLocal()
    yield db
    db.close()


def test_seed_employee_count(db_session):
    count = db_session.query(Employee).count()
    assert count >= 30, f"Expected at least 30 employees, found {count}"


def test_seed_pod_structure(db_session):
    pods = db_session.query(Pod).all()
    assert len(pods) == 4
    for pod in pods:
        assert pod.lead_id is not None
        assert len(pod.employees) >= 6


def test_seed_brands_and_processes(db_session):
    brand_count = db_session.query(Brand).count()
    process_count = db_session.query(Process).count()
    assert brand_count == 24
    assert process_count == 6


def test_public_holidays_present(db_session):
    holidays = db_session.query(PublicHoliday).all()
    assert len(holidays) >= 8

"""Normalised relational schema for RosterIQ.

Workload is measured in brands per day. Processes inside the same brand are one
person's responsibilities, not overlapping shifts.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Pod(Base):
    __tablename__ = "pods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # use_alter breaks the pod <-> employee cycle when SQLite creates tables.
    lead_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("employees.id", use_alter=True, name="fk_pods_lead_id"),
        nullable=True,
    )
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    lead: Mapped["Employee | None"] = relationship("Employee", foreign_keys=[lead_id])
    employees: Mapped[list["Employee"]] = relationship(
        "Employee",
        back_populates="pod",
        foreign_keys="Employee.pod_id",
    )
    brands: Mapped[list["Brand"]] = relationship("Brand", back_populates="pod")


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    pod_id: Mapped[int] = mapped_column(ForeignKey("pods.id"), nullable=False, index=True)
    designation: Mapped[str] = mapped_column(String(120), nullable=False)
    employment_status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    # Manager flag. Live status (on leave, weekly off) is derived.
    availability_status: Mapped[str] = mapped_column(String(32), nullable=False, default="available")
    weekly_off_preference: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    # Soft constraint. Comma-separated weekday numbers the employee prefers to avoid.
    avoid_weekdays: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    # Maximum distinct brands on one calendar day.
    max_daily_workload: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    pod: Mapped[Pod] = relationship("Pod", back_populates="employees", foreign_keys=[pod_id])
    assignments: Mapped[list["EmployeeAssignment"]] = relationship(
        "EmployeeAssignment",
        back_populates="employee",
        cascade="all, delete-orphan",
    )
    weekly_offs: Mapped[list["WeeklyOff"]] = relationship(
        "WeeklyOff",
        back_populates="employee",
        cascade="all, delete-orphan",
    )
    leaves: Mapped[list["Leave"]] = relationship(
        "Leave",
        back_populates="employee",
        cascade="all, delete-orphan",
    )
    comp_offs: Mapped[list["CompOff"]] = relationship(
        "CompOff",
        back_populates="employee",
        cascade="all, delete-orphan",
    )
    availability: Mapped[list["EmployeeAvailability"]] = relationship(
        "EmployeeAvailability",
        back_populates="employee",
        cascade="all, delete-orphan",
    )


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    pod_id: Mapped[int] = mapped_column(ForeignKey("pods.id"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    pod: Mapped[Pod] = relationship("Pod", back_populates="brands")
    rules: Mapped[list["WorkingRule"]] = relationship(
        "WorkingRule",
        back_populates="brand",
        cascade="all, delete-orphan",
    )
    coverage: Mapped[list["CoverageRequirement"]] = relationship(
        "CoverageRequirement",
        back_populates="brand",
        cascade="all, delete-orphan",
    )
    assignments: Mapped[list["EmployeeAssignment"]] = relationship(
        "EmployeeAssignment",
        back_populates="brand",
        cascade="all, delete-orphan",
    )


class Process(Base):
    __tablename__ = "processes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_predefined: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class EmployeeAssignment(Base):
    """Authorises one employee to cover one process of one brand."""

    __tablename__ = "employee_assignments"
    __table_args__ = (UniqueConstraint("employee_id", "brand_id", "process_id", name="uq_assignment"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    process_id: Mapped[int] = mapped_column(ForeignKey("processes.id", ondelete="CASCADE"), nullable=False, index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    employee: Mapped[Employee] = relationship("Employee", back_populates="assignments")
    brand: Mapped[Brand] = relationship("Brand", back_populates="assignments")
    process: Mapped[Process] = relationship("Process")


class WorkingRule(Base):
    """Brand-process operating calendar. Independent of any employee's weekly off."""

    __tablename__ = "working_rules"
    __table_args__ = (UniqueConstraint("brand_id", "process_id", name="uq_working_rule"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    process_id: Mapped[int] = mapped_column(ForeignKey("processes.id", ondelete="CASCADE"), nullable=False, index=True)
    # all_days | holidays_off | sundays_and_holidays_off | custom
    mode: Mapped[str] = mapped_column(String(40), nullable=False)
    custom_weekdays: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    # off | work — used when mode is custom
    holiday_policy: Mapped[str] = mapped_column(String(16), default="off", nullable=False)

    brand: Mapped[Brand] = relationship("Brand", back_populates="rules")
    process: Mapped[Process] = relationship("Process")


class CoverageRequirement(Base):
    """Minimum headcount for a brand-process.

    day_of_week -1 applies to every operating day. 0-6 overrides that weekday.
    """

    __tablename__ = "coverage_requirements"
    __table_args__ = (UniqueConstraint("brand_id", "process_id", "day_of_week", name="uq_coverage"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    process_id: Mapped[int] = mapped_column(ForeignKey("processes.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False, default=-1)
    min_staff: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    brand: Mapped[Brand] = relationship("Brand", back_populates="coverage")
    process: Mapped[Process] = relationship("Process")


class PublicHoliday(Base):
    __tablename__ = "public_holidays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime] = mapped_column(Date, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)


class WeeklyOff(Base):
    __tablename__ = "weekly_offs"
    __table_args__ = (UniqueConstraint("employee_id", "day_of_week", name="uq_weekly_off"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)

    employee: Mapped[Employee] = relationship("Employee", back_populates="weekly_offs")


class Leave(Base):
    __tablename__ = "leaves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    start_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    leave_type: Mapped[str] = mapped_column(String(32), nullable=False, default="planned")
    # pending | approved | rejected — only approved blocks scheduling
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    employee: Mapped[Employee] = relationship("Employee", back_populates="leaves")


class CompOff(Base):
    __tablename__ = "comp_offs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    worked_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    off_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    employee: Mapped[Employee] = relationship("Employee", back_populates="comp_offs")


class EmployeeAvailability(Base):
    """Date-specific availability that is neither a leave nor a weekly off."""

    __tablename__ = "employee_availability"
    __table_args__ = (UniqueConstraint("employee_id", "date", name="uq_availability"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    # unavailable (hard) | preferred_off (soft)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    note: Mapped[str] = mapped_column(Text, default="", nullable=False)

    employee: Mapped[Employee] = relationship("Employee", back_populates="availability")


class Roster(Base):
    __tablename__ = "rosters"
    __table_args__ = (UniqueConstraint("year", "month", name="uq_roster_month"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    # not_generated is not stored; valid | partial
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="partial")
    is_valid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    coverage_percent: Mapped[float] = mapped_column(default=0, nullable=False)
    conflict_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warning_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    entries: Mapped[list["RosterEntry"]] = relationship(
        "RosterEntry",
        back_populates="roster",
        cascade="all, delete-orphan",
    )
    conflicts: Mapped[list["SchedulingConflict"]] = relationship(
        "SchedulingConflict",
        back_populates="roster",
        cascade="all, delete-orphan",
    )


class RosterEntry(Base):
    __tablename__ = "roster_entries"
    __table_args__ = (UniqueConstraint("roster_id", "employee_id", "date", name="uq_roster_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    roster_id: Mapped[int] = mapped_column(ForeignKey("rosters.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    # working | weekly_off | public_holiday | approved_leave | comp_off | calendar_off | available | unavailable
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    on_public_holiday: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    roster: Mapped[Roster] = relationship("Roster", back_populates="entries")
    employee: Mapped[Employee] = relationship("Employee")
    brands: Mapped[list["RosterAssignment"]] = relationship(
        "RosterAssignment",
        back_populates="entry",
        cascade="all, delete-orphan",
    )


class RosterAssignment(Base):
    """A brand this employee is scheduled to cover on the entry's date."""

    __tablename__ = "roster_assignments"
    __table_args__ = (UniqueConstraint("entry_id", "brand_id", name="uq_entry_brand"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("roster_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)

    entry: Mapped[RosterEntry] = relationship("RosterEntry", back_populates="brands")
    brand: Mapped[Brand] = relationship("Brand")


class RosterOverride(Base):
    """Manager pin for a single employee-day. Hard constraints still win."""

    __tablename__ = "roster_overrides"
    __table_args__ = (UniqueConstraint("employee_id", "date", name="uq_override"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    # Comma-separated brand ids when status is working.
    brand_ids: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    note: Mapped[str] = mapped_column(Text, default="", nullable=False)

    employee: Mapped[Employee] = relationship("Employee")


class SchedulingConflict(Base):
    __tablename__ = "scheduling_conflicts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    roster_id: Mapped[int] = mapped_column(ForeignKey("rosters.id", ondelete="CASCADE"), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    conflict_type: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    brand_id: Mapped[int | None] = mapped_column(ForeignKey("brands.id", ondelete="SET NULL"), nullable=True)
    process_id: Mapped[int | None] = mapped_column(ForeignKey("processes.id", ondelete="SET NULL"), nullable=True)
    date: Mapped[datetime | None] = mapped_column(Date, nullable=True, index=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    suggestion: Mapped[str] = mapped_column(Text, default="", nullable=False)
    suggestion_action: Mapped[str] = mapped_column(Text, default="", nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    roster: Mapped[Roster] = relationship("Roster", back_populates="conflicts")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity: Mapped[str] = mapped_column(String(80), nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="", nullable=False)

"""Employees API router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Employee, EmployeeAssignment, Pod, WeeklyOff
from app.schemas import AssignmentOut, EmployeeIn, EmployeeOut

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("", response_model=list[EmployeeOut])
def list_employees(db: Session = Depends(get_db)) -> list[EmployeeOut]:
    employees = (
        db.query(Employee)
        .options(
            selectinload(Employee.pod),
            selectinload(Employee.weekly_offs),
            selectinload(Employee.assignments).selectinload(EmployeeAssignment.brand),
            selectinload(Employee.assignments).selectinload(EmployeeAssignment.process),
        )
        .order_by(Employee.pod_id, Employee.employee_code)
        .all()
    )

    output = []
    for emp in employees:
        offs = [wo.day_of_week for wo in emp.weekly_offs]
        avoids = [int(x) for x in emp.avoid_weekdays.split(",") if x.strip()]
        assignments_out = [
            AssignmentOut(
                id=a.id,
                brand_id=a.brand_id,
                brand_code=a.brand.code,
                brand_name=a.brand.name,
                process_id=a.process_id,
                process_code=a.process.code,
                process_name=a.process.name,
                is_primary=a.is_primary,
            )
            for a in emp.assignments
        ]

        output.append(
            EmployeeOut(
                id=emp.id,
                employee_code=emp.employee_code,
                full_name=emp.full_name,
                email=emp.email,
                pod_id=emp.pod_id,
                pod_name=emp.pod.name if emp.pod else "",
                pod_code=emp.pod.code if emp.pod else "",
                designation=emp.designation,
                employment_status=emp.employment_status,
                availability_status=emp.availability_status,
                today_status="available",
                weekly_off_preference=emp.weekly_off_preference,
                weekly_offs=offs,
                avoid_weekdays=avoids,
                max_daily_workload=emp.max_daily_workload,
                notes=emp.notes,
                is_pod_lead=emp.pod and emp.pod.lead_id == emp.id,
                assignments=assignments_out,
            )
        )
    return output


@router.get("/{employee_id}", response_model=EmployeeOut)
def get_employee(employee_id: int, db: Session = Depends(get_db)) -> EmployeeOut:
    emp = (
        db.query(Employee)
        .filter(Employee.id == employee_id)
        .options(
            selectinload(Employee.pod),
            selectinload(Employee.weekly_offs),
            selectinload(Employee.assignments).selectinload(EmployeeAssignment.brand),
            selectinload(Employee.assignments).selectinload(EmployeeAssignment.process),
        )
        .first()
    )
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    offs = [wo.day_of_week for wo in emp.weekly_offs]
    avoids = [int(x) for x in emp.avoid_weekdays.split(",") if x.strip()]
    assignments_out = [
        AssignmentOut(
            id=a.id,
            brand_id=a.brand_id,
            brand_code=a.brand.code,
            brand_name=a.brand.name,
            process_id=a.process_id,
            process_code=a.process.code,
            process_name=a.process.name,
            is_primary=a.is_primary,
        )
        for a in emp.assignments
    ]

    return EmployeeOut(
        id=emp.id,
        employee_code=emp.employee_code,
        full_name=emp.full_name,
        email=emp.email,
        pod_id=emp.pod_id,
        pod_name=emp.pod.name if emp.pod else "",
        pod_code=emp.pod.code if emp.pod else "",
        designation=emp.designation,
        employment_status=emp.employment_status,
        availability_status=emp.availability_status,
        today_status="available",
        weekly_off_preference=emp.weekly_off_preference,
        weekly_offs=offs,
        avoid_weekdays=avoids,
        max_daily_workload=emp.max_daily_workload,
        notes=emp.notes,
        is_pod_lead=emp.pod and emp.pod.lead_id == emp.id,
        assignments=assignments_out,
    )

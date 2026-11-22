"""Pods and Brands API router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Brand, Employee, EmployeeAssignment, Pod, Process, WorkingRule
from app.schemas import BrandOut, PodOut, ProcessOut, RuleOut

pods_router = APIRouter(prefix="/pods", tags=["Pods"])
brands_router = APIRouter(prefix="/brands", tags=["Brands"])
processes_router = APIRouter(prefix="/processes", tags=["Processes"])


@pods_router.get("", response_model=list[PodOut])
def list_pods(db: Session = Depends(get_db)) -> list[PodOut]:
    pods = (
        db.query(Pod)
        .options(
            selectinload(Pod.lead),
            selectinload(Pod.employees),
            selectinload(Pod.brands),
        )
        .order_by(Pod.code)
        .all()
    )

    output = []
    for pod in pods:
        emp_list = [{"id": e.id, "name": e.full_name, "code": e.employee_code, "role": e.designation} for e in pod.employees]
        brand_list = [{"id": b.id, "name": b.name, "code": b.code} for b in pod.brands]
        output.append(
            PodOut(
                id=pod.id,
                code=pod.code,
                name=pod.name,
                lead_id=pod.lead_id,
                lead_name=pod.lead.full_name if pod.lead else None,
                lead_code=pod.lead.employee_code if pod.lead else None,
                notes=pod.notes,
                employee_count=len(pod.employees),
                employees=emp_list,
                brands=brand_list,
            )
        )
    return output


@brands_router.get("", response_model=list[BrandOut])
def list_brands(db: Session = Depends(get_db)) -> list[BrandOut]:
    brands = (
        db.query(Brand)
        .options(
            selectinload(Brand.pod),
            selectinload(Brand.rules).selectinload(WorkingRule.process),
            selectinload(Brand.assignments).selectinload(EmployeeAssignment.employee),
        )
        .order_by(Brand.pod_id, Brand.name)
        .all()
    )

    output = []
    for b in brands:
        unique_emps = {a.employee for a in b.assignments if a.employee}
        emp_list = [{"id": e.id, "name": e.full_name, "code": e.employee_code} for e in sorted(unique_emps, key=lambda x: x.employee_code)]
        rules_out = [
            RuleOut(
                id=r.id,
                process_id=r.process_id,
                process_code=r.process.code,
                process_name=r.process.name,
                mode=r.mode,
                custom_weekdays=[int(x) for x in r.custom_weekdays.split(",") if x.strip()],
                holiday_policy=r.holiday_policy,
                min_staff=1,
            )
            for r in b.rules
        ]

        output.append(
            BrandOut(
                id=b.id,
                code=b.code,
                name=b.name,
                pod_id=b.pod_id,
                pod_name=b.pod.name if b.pod else "",
                description=b.description,
                employee_count=len(emp_list),
                employees=emp_list,
                rules=rules_out,
            )
        )
    return output


@processes_router.get("", response_model=list[ProcessOut])
def list_processes(db: Session = Depends(get_db)) -> list[ProcessOut]:
    processes = db.query(Process).order_by(Process.id).all()
    return [
        ProcessOut(
            id=p.id,
            code=p.code,
            name=p.name,
            description=p.description,
            is_predefined=p.is_predefined,
            assignment_count=0,
        )
        for p in processes
    ]

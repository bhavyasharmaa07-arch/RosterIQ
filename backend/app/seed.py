"""Realistic sample organisation, loaded once when the database is empty.

About 80% of brands have one dedicated employee. Weekly offs on those brands
are aligned with the brand calendar so the baseline roster is feasible.
A few deliberate exceptions (leave, comp-off, a weekly off that cuts across an
operating day, and a minimum of two people) produce real conflicts.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models import (
    AuditLog,
    Brand,
    CompOff,
    CoverageRequirement,
    Employee,
    EmployeeAssignment,
    Leave,
    Pod,
    Process,
    PublicHoliday,
    WeeklyOff,
    WorkingRule,
)
from app.services.scheduler import generate_roster

PROCESSES = [
    ("CS", "Customer Support", "Inbound queries, order tracking and issue resolution.", True),
    ("ACC", "Abandoned Cart Conversion", "Follow-up with shoppers who left a cart unpaid.", True),
    ("NDR", "Non-Delivery Report Management", "Resolve failed delivery reports with the courier and the customer.", True),
    ("RET", "Retention", "Save at-risk subscribers and repeat buyers.", True),
    ("OTH", "Other", "Brand-specific operational work that does not fit the core processes.", True),
    ("ESC", "Social Escalation", "Public social-channel escalations added by the operations team.", False),
]

PODS = [
    ("POD-N", "North Star Pod"),
    ("POD-W", "Western Circuit Pod"),
    ("POD-S", "Southern Crest Pod"),
    ("POD-C", "Central Ops Pod"),
]

# code, name, pod, weekly off (0=Mon .. 6=Sun), designation, workload, status
EMPLOYEES = [
    ("EMP001", "Ananya Sharma", "POD-N", 6, "Pod Lead", 1, "active"),
    ("EMP002", "Rohan Mehta", "POD-N", 6, "Process Associate", 1, "active"),
    ("EMP003", "Priya Nair", "POD-N", 6, "Process Associate", 1, "active"),
    ("EMP004", "Arjun Reddy", "POD-N", 6, "Brand Specialist", 1, "active"),
    ("EMP005", "Neha Kapoor", "POD-N", 0, "Process Associate", 1, "active"),
    ("EMP006", "Vikram Singh", "POD-N", 6, "Senior Process Associate", 1, "active"),
    ("EMP007", "Meera Joshi", "POD-W", 6, "Pod Lead", 1, "active"),
    ("EMP008", "Aditya Verma", "POD-W", 6, "Process Associate", 1, "active"),
    ("EMP009", "Pooja Deshmukh", "POD-W", 0, "Brand Specialist", 1, "active"),
    ("EMP010", "Rahul Gupta", "POD-W", 6, "Process Associate", 1, "active"),
    ("EMP011", "Anjali Menon", "POD-W", 6, "Process Associate", 1, "active"),
    ("EMP012", "Siddharth Rao", "POD-W", 0, "Senior Process Associate", 1, "active"),
    ("EMP013", "Kabir Khan", "POD-S", 6, "Pod Lead", 1, "active"),
    ("EMP014", "Lakshmi Krishnan", "POD-S", 6, "Process Associate", 1, "active"),
    ("EMP015", "Tanvi Shah", "POD-S", 6, "Brand Specialist", 1, "active"),
    ("EMP016", "Harsh Patel", "POD-S", 0, "Process Associate", 1, "active"),
    ("EMP017", "Riya Bose", "POD-C", 6, "Pod Lead", 1, "active"),
    ("EMP018", "Nikhil Jain", "POD-C", 2, "Process Associate", 1, "active"),
    ("EMP019", "Aisha Khan", "POD-C", 6, "Brand Specialist", 1, "on_notice"),
    ("EMP020", "Sneha Iyer", "POD-N", 6, "Senior Process Associate", 2, "active"),
    ("EMP021", "Karan Malhotra", "POD-N", 2, "Process Associate", 1, "active"),
    ("EMP022", "Divya Choudhary", "POD-W", 4, "Process Associate", 1, "active"),
    ("EMP023", "Ishaan Banerjee", "POD-W", 1, "Process Associate", 1, "active"),
    ("EMP024", "Myra D'Souza", "POD-S", 6, "Senior Process Associate", 1, "active"),
    ("EMP025", "Varun Khanna", "POD-S", 6, "Process Associate", 1, "active"),
    ("EMP026", "Aditi Bansal", "POD-S", 6, "Process Associate", 1, "active"),
    ("EMP027", "Manav Agarwal", "POD-C", 0, "Process Associate", 1, "active"),
    ("EMP028", "Shreya Pillai", "POD-C", 6, "Brand Specialist", 1, "active"),
    ("EMP029", "Dev Sharma", "POD-C", 6, "Process Associate", 1, "active"),
    ("EMP030", "Nandini Rao", "POD-C", 3, "Process Associate", 1, "active"),
]

LEADS = {"POD-N": "EMP001", "POD-W": "EMP007", "POD-S": "EMP013", "POD-C": "EMP017"}

# Brands whose dedicated employee is off on Monday, so the calendar is closed that day.
MONDAY_CLOSED = {"CraftCart", "MetroBasket", "KidLoom", "ChaiMistry"}

BRANDS = [
    ("UrbanThread", "UrbanThread", "POD-N", "Apparel marketplace with a single dedicated owner for every process."),
    ("SpiceRoute", "SpiceRoute Kitchen", "POD-N", "Regional meal-kit brand."),
    ("HimalayanBrew", "Himalayan Brew Co", "POD-N", "Tea and coffee subscription."),
    ("LumenBeauty", "Lumen Beauty", "POD-N", "Clean beauty label."),
    ("CraftCart", "CraftCart India", "POD-N", "Handmade home goods. Closed Mondays."),
    ("DailyDabba", "DailyDabba", "POD-N", "Tiffin subscription."),
    ("FitNest", "FitNest Athletics", "POD-W", "Training apparel and equipment."),
    ("PearlDrop", "PearlDrop Skincare", "POD-W", "Clinical skincare."),
    ("MetroBasket", "MetroBasket", "POD-W", "City grocery delivery. Closed Mondays."),
    ("SaffronCo", "Saffron & Co", "POD-W", "Premium pantry staples."),
    ("BlueTokri", "BlueTokri", "POD-W", "Artisan marketplace."),
    ("KidLoom", "KidLoom", "POD-W", "Children's clothing. Closed Mondays."),
    ("VoltMobility", "VoltMobility", "POD-S", "Electric scooter accessories."),
    ("GreenHarvest", "GreenHarvest Organics", "POD-S", "Organic grocery."),
    ("AuraHome", "AuraHome", "POD-S", "Home fragrance and linen."),
    ("ChaiMistry", "ChaiMistry", "POD-S", "Specialty chai. Closed Mondays."),
    ("NomadFootwear", "NomadFootwear", "POD-C", "Everyday footwear."),
    ("Pawsome", "Pawsome India", "POD-C", "Pet care. CS stays open on the owner's weekly off, which leaves a gap."),
    ("SilkRoute", "SilkRoute Apparel", "POD-C", "Occasion wear, including the added social escalation process."),
    ("FreshBowl", "FreshBowl Foods", "POD-N", "Multi-person meal brand. ACC runs every day of the year."),
    ("GlowTheory", "GlowTheory", "POD-W", "Multi-person beauty brand. CS works through public holidays."),
    ("QuickCart", "QuickCart Express", "POD-S", "Multi-person quick commerce. CS needs two people."),
    ("NestLiving", "NestLiving", "POD-C", "Multi-person home brand with split process ownership."),
    ("BharatAudio", "BharatAudio", "POD-C", "Multi-person audio brand."),
]

# employee code -> list of (brand code, process code, is_primary)
ASSIGNMENTS: dict[str, list[tuple[str, str, bool]]] = {
    "EMP001": [("UrbanThread", code, True) for code in ("CS", "ACC", "NDR", "RET", "OTH")],
    "EMP002": [("SpiceRoute", code, True) for code in ("CS", "ACC", "NDR")],
    "EMP003": [("HimalayanBrew", code, True) for code in ("CS", "ACC", "NDR", "RET")],
    "EMP004": [("LumenBeauty", code, True) for code in ("CS", "ACC", "NDR")],
    "EMP005": [("CraftCart", code, True) for code in ("CS", "ACC", "NDR")],
    "EMP006": [("DailyDabba", code, True) for code in ("CS", "ACC", "NDR", "RET")],
    "EMP007": [("FitNest", code, True) for code in ("CS", "ACC", "NDR")],
    "EMP008": [("PearlDrop", code, True) for code in ("CS", "ACC", "NDR")],
    "EMP009": [("MetroBasket", code, True) for code in ("CS", "ACC", "NDR", "RET")],
    "EMP010": [("SaffronCo", code, True) for code in ("CS", "ACC", "NDR")],
    "EMP011": [("BlueTokri", code, True) for code in ("CS", "ACC", "NDR")],
    "EMP012": [("KidLoom", code, True) for code in ("CS", "ACC", "NDR", "RET")],
    "EMP013": [("VoltMobility", code, True) for code in ("CS", "ACC", "NDR")],
    "EMP014": [("GreenHarvest", code, True) for code in ("CS", "ACC", "NDR", "RET")],
    "EMP015": [("AuraHome", code, True) for code in ("CS", "ACC", "NDR")],
    "EMP016": [("ChaiMistry", code, True) for code in ("CS", "ACC", "NDR")],
    "EMP017": [("NomadFootwear", code, True) for code in ("CS", "ACC", "NDR", "RET")],
    "EMP018": [("Pawsome", code, True) for code in ("CS", "ACC", "NDR")],
    "EMP019": [("SilkRoute", code, True) for code in ("CS", "ACC", "NDR", "RET", "ESC")],
    "EMP020": [("FreshBowl", code, True) for code in ("CS", "ACC")],
    "EMP021": [("FreshBowl", code, True) for code in ("ACC", "NDR")],
    "EMP022": [("FreshBowl", code, True) for code in ("CS", "NDR", "RET")],
    "EMP023": [("GlowTheory", code, True) for code in ("CS", "ACC")],
    "EMP024": [("GlowTheory", code, True) for code in ("CS", "ACC", "NDR", "RET")],
    "EMP025": [("QuickCart", code, True) for code in ("CS", "ACC", "NDR")],
    "EMP026": [("QuickCart", code, True) for code in ("CS", "RET", "OTH")],
    "EMP027": [("NestLiving", code, True) for code in ("CS", "ACC")],
    "EMP028": [("NestLiving", code, True) for code in ("NDR", "RET", "OTH")],
    "EMP029": [("BharatAudio", code, True) for code in ("CS", "ACC", "NDR")],
    "EMP030": [("BharatAudio", code, True) for code in ("CS", "RET")],
}

# (brand, process) -> (mode, custom weekdays, holiday policy, min staff)
# Anything not listed uses the brand default.
SPECIAL_RULES: dict[tuple[str, str], tuple[str, str, str, int]] = {
    ("Pawsome", "ACC"): ("custom", "0,1,3,4,5", "off", 1),
    ("Pawsome", "NDR"): ("custom", "0,1,3,4,5", "off", 1),
    ("FreshBowl", "ACC"): ("all_days", "", "work", 1),
    ("FreshBowl", "NDR"): ("holidays_off", "", "off", 1),
    ("FreshBowl", "RET"): ("custom", "0,1,2,3,5", "off", 1),
    ("GlowTheory", "CS"): ("holidays_off", "", "off", 1),
    ("GlowTheory", "ACC"): ("all_days", "", "work", 1),
    ("NestLiving", "CS"): ("custom", "1,2,3,4,5", "off", 1),
    ("NestLiving", "ACC"): ("custom", "1,2,3,4,5,6", "off", 1),
    ("QuickCart", "CS"): ("sundays_and_holidays_off", "", "off", 2),
    ("BharatAudio", "RET"): ("custom", "0,1,2,4,5", "off", 1),
}

HOLIDAYS = [
    (date(2026, 1, 26), "Republic Day"),
    (date(2026, 3, 4), "Holi"),
    (date(2026, 8, 15), "Independence Day"),
    (date(2026, 10, 2), "Gandhi Jayanti"),
    (date(2026, 10, 20), "Dussehra"),
    (date(2026, 11, 8), "Diwali"),
    (date(2026, 11, 24), "Guru Nanak Jayanti"),
    (date(2026, 12, 25), "Christmas"),
]


def _rule(brand_code: str, process_code: str) -> tuple[str, str, str, int]:
    special = SPECIAL_RULES.get((brand_code, process_code))
    if special:
        return special
    if brand_code in MONDAY_CLOSED:
        return ("custom", "1,2,3,4,5,6", "off", 1)
    return ("sundays_and_holidays_off", "", "off", 1)


def seed_if_empty(db: Session | None = None) -> bool:
    own_session = db is None
    if own_session:
        if SessionLocal is None:
            init_db()
        db = SessionLocal()
    assert db is not None
    try:
        if db.query(Employee).first():
            return False
        _load(db)
        if own_session:
            db.commit()
        return True
    finally:
        if own_session:
            db.close()


def _load(db: Session) -> None:
    processes = {}
    for code, name, description, predefined in PROCESSES:
        row = Process(code=code, name=name, description=description, is_predefined=predefined)
        db.add(row)
        processes[code] = row
    db.flush()

    pods = {}
    for code, name in PODS:
        row = Pod(code=code, name=name, notes="Sample operations pod.")
        db.add(row)
        pods[code] = row
    db.flush()

    employees = {}
    for code, name, pod_code, off, designation, workload, status in EMPLOYEES:
        email = code.lower() + "." + name.split()[0].lower().replace("'", "") + "@rosteriq.example"
        row = Employee(
            employee_code=code,
            full_name=name,
            email=email,
            pod_id=pods[pod_code].id,
            designation=designation,
            employment_status=status,
            availability_status="available",
            weekly_off_preference=off,
            avoid_weekdays="",
            max_daily_workload=workload,
            notes="Sample employee for the November 2026 roster.",
        )
        db.add(row)
        employees[code] = row
    db.flush()

    for code, name, pod_code, off, _designation, _workload, _status in EMPLOYEES:
        db.add(WeeklyOff(employee_id=employees[code].id, day_of_week=off))
    for pod_code, employee_code in LEADS.items():
        pods[pod_code].lead_id = employees[employee_code].id
    db.flush()

    brands = {}
    for code, name, pod_code, description in BRANDS:
        row = Brand(code=code, name=name, pod_id=pods[pod_code].id, description=description)
        db.add(row)
        brands[code] = row
    db.flush()

    seen_pairs: set[tuple[str, str]] = set()
    for employee_code, rows in ASSIGNMENTS.items():
        for brand_code, process_code, is_primary in rows:
            db.add(
                EmployeeAssignment(
                    employee_id=employees[employee_code].id,
                    brand_id=brands[brand_code].id,
                    process_id=processes[process_code].id,
                    is_primary=is_primary,
                )
            )
            seen_pairs.add((brand_code, process_code))
    db.flush()

    for brand_code, process_code in sorted(seen_pairs):
        mode, custom, holiday_policy, minimum = _rule(brand_code, process_code)
        db.add(
            WorkingRule(
                brand_id=brands[brand_code].id,
                process_id=processes[process_code].id,
                mode=mode,
                custom_weekdays=custom,
                holiday_policy=holiday_policy,
            )
        )
        db.add(
            CoverageRequirement(
                brand_id=brands[brand_code].id,
                process_id=processes[process_code].id,
                day_of_week=-1,
                min_staff=minimum,
            )
        )

    for holiday_date, holiday_name in HOLIDAYS:
        db.add(PublicHoliday(date=holiday_date, name=holiday_name))

    db.add(
        Leave(
            employee_id=employees["EMP022"].id,
            start_date=date(2026, 11, 22),
            end_date=date(2026, 11, 23),
            leave_type="planned",
            status="approved",
            reason="Family function. FreshBowl Retention has no second owner on 23 Nov.",
        )
    )
    db.add(
        Leave(
            employee_id=employees["EMP026"].id,
            start_date=date(2026, 11, 18),
            end_date=date(2026, 11, 18),
            leave_type="sick",
            status="approved",
            reason="Sick leave. QuickCart CS drops below its minimum of two.",
        )
    )
    db.add(
        Leave(
            employee_id=employees["EMP028"].id,
            start_date=date(2026, 11, 12),
            end_date=date(2026, 11, 12),
            leave_type="planned",
            status="approved",
            reason="Approved personal leave. NestLiving NDR, Retention and Other are uncovered.",
        )
    )
    db.add(
        Leave(
            employee_id=employees["EMP002"].id,
            start_date=date(2026, 11, 27),
            end_date=date(2026, 11, 27),
            leave_type="planned",
            status="pending",
            reason="Pending request. Must not block the roster until a manager approves it.",
        )
    )
    db.add(
        CompOff(
            employee_id=employees["EMP018"].id,
            worked_date=date(2026, 10, 31),
            off_date=date(2026, 11, 16),
            status="approved",
            reason="Comp-off for the 31 Oct inventory count. Pawsome has no backup that Monday.",
        )
    )
    db.add(
        CompOff(
            employee_id=employees["EMP007"].id,
            worked_date=date(2026, 11, 8),
            off_date=date(2026, 12, 1),
            status="pending",
            reason="Pending comp-off. December is not blocked until this is approved.",
        )
    )
    db.add(
        AuditLog(
            action="seed",
            entity="organisation",
            detail="Loaded 30 employees, 4 pods, 24 brands and the 2026 holiday calendar.",
        )
    )
    db.flush()

    today = date.today()
    generate_roster(db, today.year, today.month)
    db.add(
        AuditLog(
            action="generate_roster",
            entity="roster",
            detail=f"Generated the {today.strftime('%B %Y')} roster from the sample organisation.",
        )
    )
    db.flush()


if __name__ == "__main__":
    init_db()
    created = seed_if_empty()
    print("Seeded." if created else "Database already had employees; nothing was changed.")

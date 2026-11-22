# RosterIQ — Autonomous CX Workforce Scheduling & Compliance Engine

RosterIQ is a full-stack workforce planning, shift scheduling, and constraint satisfaction system designed for high-availability D2C customer experience (CX) and e-commerce pod operations (DataStraw assessment model).

---

## Architecture Overview

* **Backend**: FastAPI, SQLAlchemy 2.0, SQLite (PRAGMA foreign keys enforced), Pydantic v2, OpenPyXL, Pytest.
* **Frontend**: React 18, TypeScript, Tailwind CSS, Lucide Icons, Vite 6.
* **Domain Model**:
  * **Pods**: Dedicated business units (North Star Pod, Western Circuit Pod, Southern Crest Pod, Central Ops Pod) each managed by a Pod Lead.
  * **Brands**: 24 D2C eCommerce client brands assigned to pods.
  * **Processes**: Core CX workflows per brand: Customer Support (CS), Abandoned Cart Conversion (ACC), Non-Delivery Report Management (NDR), Retention (RET), Other (OTH), Social Escalation (ESC).
  * **Operating Calendars**: Per-brand-process operating rules (`all_days`, `sundays_and_holidays_off`, `holidays_off`, `custom` weekdays).
  * **Employees**: 30 realistic team members with designations, workload caps (brand-days per day limit), weekly off preferences, and avoided weekdays.
  * **Scheduling Algorithm**: Deterministic constraint solver that balances fairness, honors leaves and comp-offs, identifies coverage deficits, and generates intelligent colleague recommendations.

---

## Core Implemented Views

1. **Executive Dashboard**:
   * Live operational KPIs: Coverage %, Active vs. Total Staff, Total Pods/Brands/Processes, Approved Absences.
   * Brand Coverage compliance breakdown with individual fulfillment rates.
   * Shift status mix distribution (Working, Weekly Off, Leave, Comp-off, Public Holiday, Unavailable).
   * Approved employee absence roster for the month.
   * Immutable system & manager audit log.

2. **Interactive Monthly Roster Grid**:
   * 30-day sticky grid displaying each employee's schedule.
   * Color-coded status badges: Working (with brand tags), Weekly Off, Approved Leave, Comp-Off, Holiday, Unavailable.
   * Visual conflict gap indicator on affected employee-day cells.
   * Filters by Operational Pod and Search by employee name/code.

3. **Brand Coverage Matrix**:
   * Dual-view matrix displaying required vs. assigned staff for every brand-process pair across the month.
   * Visual indicators: Green (Fulfilled ≥ Min Staff), Red Alert (Headcount Gap / Deficit), Gray (Closed / Non-operating calendar day).

4. **Conflict and Recommendation Drawer**:
   * Detailed breakdown of all detected scheduling conflicts categorized by severity (Critical, High, Warning).
   * Exact constraint explanation (e.g. employee on notice, workload cap exceeded, single-owner absence).
   * AI/Engine recommendation suggesting specific colleagues in the same or adjacent pods with spare capacity.
   * One-click **"Authorize & Assign"** resolution that grants process authorization, re-solves the schedule, and eliminates the conflict.

5. **What-If Manager Override Simulation**:
   * Test schedule changes before committing to the database.
   * Preview projected coverage % delta, conflict resolution count, and constraint compliance.
   * One-click commit to persist the manager override.

6. **Personnel Absence & Leave Approvals**:
   * Review pending leave and comp-off requests.
   * One-click Approve or Reject with instant reactive recalculation of the schedule.

7. **Excel Export**:
   * Download styled `.xlsx` workbooks containing Employee Schedules, Brand Coverage matrices, and Conflict logs.

---

## Running the Application

### 1. Run the Backend
```bash
# In one terminal:
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
* Interactive API Documentation: http://127.0.0.1:8000/docs
* Health Check: http://127.0.0.1:8000/api/health

### 2. Run the Frontend
```bash
# In a second terminal:
cd frontend
npm run dev
```
* Web Application: http://localhost:5173

### 3. Run Automated Tests
```bash
cd backend
pytest -v
```
All 14 unit and integration tests covering database models, the scheduling engine, and API endpoints pass automatically.

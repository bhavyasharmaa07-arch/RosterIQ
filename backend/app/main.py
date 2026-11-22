"""FastAPI Application entrypoint for RosterIQ."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.seed import seed_if_empty
from app.routers.dashboard import router as dashboard_router
from app.routers.roster import router as roster_router
from app.routers.conflicts import router as conflicts_router
from app.routers.overrides import router as overrides_router
from app.routers.employees import router as employees_router
from app.routers.pods import pods_router, brands_router, processes_router
from app.routers.leaves import leaves_router, compoffs_router
from app.routers.audit import router as audit_router


# Ensure tables and seed exist on module load
init_db()
seed_if_empty()

app = FastAPI(
    title="RosterIQ API",
    description="Automated Constraint-Aware Workforce Scheduling & CX Pod Management Engine",
    version="1.0.0",
)

# Enable CORS for local dev frontend (Vite defaults to 5173 or 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Sub-routers
app.include_router(dashboard_router, prefix="/api")
app.include_router(roster_router, prefix="/api")
app.include_router(conflicts_router, prefix="/api")
app.include_router(overrides_router, prefix="/api")
app.include_router(employees_router, prefix="/api")
app.include_router(pods_router, prefix="/api")
app.include_router(brands_router, prefix="/api")
app.include_router(processes_router, prefix="/api")
app.include_router(leaves_router, prefix="/api")
app.include_router(compoffs_router, prefix="/api")
app.include_router(audit_router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "RosterIQ", "version": "1.0.0"}


@app.get("/")
def root():
    return {
        "message": "Welcome to RosterIQ API. Visit /docs for interactive OpenAPI documentation.",
        "health": "/api/health",
        "docs": "/docs",
    }

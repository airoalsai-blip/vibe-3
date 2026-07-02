from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.alerts import router as alerts_router
from app.api.routes.departments import router as departments_router
from app.api.routes.imports import router as imports_router
from app.api.routes.employees import router as employees_router
from app.api.routes.manual_entries import router as manual_entries_router
from app.api.routes.health import router as health_router
from app.api.routes.policies import router as policies_router
from app.api.routes.regions import router as regions_router
from app.api.routes.weather import router as weather_router
from app.core.database import init_db


app = FastAPI(title="Weather Duty Alert", version="0.1.0")
init_db()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(departments_router)
app.include_router(imports_router)
app.include_router(manual_entries_router)
app.include_router(regions_router)
app.include_router(weather_router)
app.include_router(employees_router)
app.include_router(policies_router)
app.include_router(alerts_router)

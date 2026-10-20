from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.core.database import engine
from app.core.migrations import schema_current
from app.schemas import HealthCheck
from app.core.config import settings
from app.api.v1.auth import router as auth_router
from app.api.v1.resume import router as resume_router
from app.api.v1.coach import router as coach_router
from app.api.v1.interview import router as interview_router
from app.api.v1.reports import router as reports_router
from app.api.v1.settings import router as settings_router
from app.api.v1.admin import router as admin_router

api_router = APIRouter()

# Health
@api_router.get("/health", response_model=HealthCheck, tags=["Health"])
def health_check():
    return HealthCheck(status="healthy", project="CareerMind AI", version=settings.VERSION)

@api_router.get("/ready", tags=["Health"])
def readiness():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT id FROM users LIMIT 0"))
            if not schema_current(connection):
                return JSONResponse({"status": "unavailable"}, status_code=503)
        return {"status": "ready"}
    except Exception:
        return JSONResponse({"status": "unavailable"}, status_code=503)

# Include v1 Domain Routers
api_router.include_router(auth_router)
api_router.include_router(resume_router)
api_router.include_router(coach_router)
api_router.include_router(interview_router)
api_router.include_router(reports_router)
api_router.include_router(settings_router)
api_router.include_router(admin_router)

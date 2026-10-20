import os
from contextlib import asynccontextmanager
from app.services.research_worker import start_dispatcher
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, SessionLocal
from app.core.migrations import migrate
from app.core.security import verify_password
from app.api import api_router
from app.models import User
from app.core.request_limits import RequestLimitsMiddleware

@asynccontextmanager
async def lifespan(app):
    migrate(engine)
    retire_public_accounts()
    stop = start_dispatcher()
    yield
    stop.set()

app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Production-grade AI Career Operating System backend API powered by FastAPI, SQLAlchemy & Gemini."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLimitsMiddleware)

# Retire previously seeded accounts only while they still use public credentials.
# Accounts with an independently changed password are preserved.
def retire_public_accounts():
    with SessionLocal() as db:
        for email, password in [("demo@careermind.ai", "Password123!"), ("admin@careermind.ai", "AdminPass123!")]:
            user = db.query(User).filter(User.email == email).first()
            if user and (user.hashed_password == "standalone-mode" or verify_password(password, user.hashed_password)):
                user.is_active = False
                user.is_superuser = False
        db.commit()

@app.middleware("http")
async def response_security(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    if request.url.path.startswith(settings.API_V1_STR):
        response.headers["Cache-Control"] = "no-store"
    return response

# Mount API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Next.js serves the UI in development and production. Static hosting is opt-in
# to avoid silently serving the obsolete checked-in frontend/out build.
STATIC_DIR = os.getenv("STATIC_FRONTEND_DIR")

if STATIC_DIR and os.path.exists(os.path.join(STATIC_DIR, "index.html")):
    _next_dir = os.path.join(STATIC_DIR, "_next")
    if os.path.exists(_next_dir):
        app.mount("/_next", StaticFiles(directory=_next_dir), name="next_assets")

    @app.get("/{full_path:path}")
    async def serve_spa_or_api(request: Request, full_path: str = ""):
        # Do not intercept API or docs routes
        if full_path.startswith("api/") or full_path in ("docs", "openapi.json"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})

        clean_path = full_path.strip("/")

        root_path = os.path.realpath(STATIC_DIR)
        candidates = [clean_path, os.path.join(clean_path, "index.html"), clean_path + ".html"] if clean_path else ["index.html"]
        for relative in candidates:
            candidate = os.path.realpath(os.path.join(root_path, relative))
            try:
                inside = os.path.commonpath([root_path, candidate]) == root_path
            except ValueError:
                inside = False
            if not inside:
                return JSONResponse(status_code=404, content={"detail": "Not found"})
            if os.path.isfile(candidate):
                return FileResponse(candidate)
        return JSONResponse(status_code=404, content={"detail": "Not found"})

else:
    @app.get("/")
    def root():
        return {
            "message": "Welcome to NexPath AI Career Operating System API",
            "docs": "/docs",
            "health": f"{settings.API_V1_STR}/health"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

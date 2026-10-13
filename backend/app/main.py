import os
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.core.security import verify_password
from app.api import api_router
from app.models import User

app = FastAPI(
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

Base.metadata.create_all(bind=engine)


# Retire previously seeded accounts only while they still use public credentials.
# Accounts with an independently changed password are preserved.
with SessionLocal() as db:
    for email, password in [("demo@careermind.ai", "Password123!"), ("admin@careermind.ai", "AdminPass123!")]:
        user = db.query(User).filter(User.email == email).first()
        if user and (user.hashed_password == "standalone-mode" or verify_password(password, user.hashed_password)):
            user.is_active = False
            user.is_superuser = False
    db.commit()

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
        candidate = os.path.realpath(os.path.join(root_path, clean_path))
        if os.path.commonpath([root_path, candidate]) != root_path:
            return JSONResponse(status_code=404, content={"detail": "Not found"})

        # 1. Root route
        if not clean_path:
            return FileResponse(os.path.join(STATIC_DIR, "index.html"))

        # 2. Exact file (e.g. favicon.ico, images, .txt)
        file_path = os.path.join(STATIC_DIR, clean_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)

        # 3. Directory with index.html (e.g. login/index.html, dashboard/index.html)
        dir_html = os.path.join(STATIC_DIR, clean_path, "index.html")
        if os.path.isfile(dir_html):
            return FileResponse(dir_html)

        # 4. Suffix .html (e.g. login.html, dashboard.html)
        html_path = os.path.join(STATIC_DIR, f"{clean_path}.html")
        if os.path.isfile(html_path):
            return FileResponse(html_path)

        # 5. SPA fallback
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
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

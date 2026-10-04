import os
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.core.security import get_password_hash
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


def seed_default_users():
    """Automatically seed default demo and admin superuser accounts safely."""
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == "demo@careermind.ai").first():
            demo = User(
                email="demo@careermind.ai",
                full_name="Demo Professional",
                hashed_password=get_password_hash("Password123!"),
                is_active=True,
                is_superuser=False
            )
            db.add(demo)

        admin = db.query(User).filter(User.email == "admin@careermind.ai").first()
        if not admin:
            admin_user = User(
                email="admin@careermind.ai",
                full_name="System Administrator",
                hashed_password=get_password_hash("AdminPass123!"),
                is_active=True,
                is_superuser=True
            )
            db.add(admin_user)
        elif not admin.is_superuser:
            admin.is_superuser = True

        db.commit()
    except Exception as e:
        print(f"Error seeding default accounts: {e}")
    finally:
        db.close()


seed_default_users()

# Mount API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Determine path to compiled Next.js static files
POSSIBLE_STATIC_DIRS = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "out")),
    "/app/frontend/out",
    os.path.abspath(os.path.join(os.getcwd(), "frontend", "out")),
    os.path.abspath(os.path.join(os.getcwd(), "..", "frontend", "out")),
]

STATIC_DIR = next((d for d in POSSIBLE_STATIC_DIRS if os.path.exists(d) and os.path.isdir(d)), None)

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

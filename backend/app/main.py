from fastapi import FastAPI
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
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"https?://.*",
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

app.include_router(api_router, prefix=settings.API_V1_STR)


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

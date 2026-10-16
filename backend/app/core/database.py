from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Normalize provider-generated PostgreSQL URLs to the installed driver.
database_url = settings.DATABASE_URL
if database_url.startswith(("postgres://", "postgresql://")):
    database_url = "postgresql+psycopg://" + database_url.split("://", 1)[1]

# Configure engine based on SQLite vs PostgreSQL
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False, "timeout": 3}

if database_url.startswith("postgresql"):
    connect_args["connect_timeout"] = 3
    connect_args["options"] = "-c statement_timeout=3000 -c lock_timeout=3000"

engine = create_engine(
    database_url,
    connect_args=connect_args,
    **({"pool_timeout": 3} if database_url not in ("sqlite://", "sqlite:///:memory:") else {}),
    pool_pre_ping=True if not settings.DATABASE_URL.startswith("sqlite") else False,
)

if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    """Dependency for acquiring a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

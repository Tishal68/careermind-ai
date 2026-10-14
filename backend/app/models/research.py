from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from app.core.database import Base


class ResearchJob(Base):
    __tablename__ = "research_jobs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending")
    request_data = Column(JSON, nullable=False)
    report_id = Column(Integer, ForeignKey("career_reports.id"), nullable=True)
    error = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ResearchSlot(Base):
    __tablename__ = "research_slots"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    job_id = Column(Integer, ForeignKey("research_jobs.id", ondelete="SET NULL"), nullable=True)


class ResearchSubmission(Base):
    __tablename__ = "research_submissions"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    request_key = Column(String(64), primary_key=True)
    fingerprint = Column(String(64), nullable=False)
    job_id = Column(Integer, ForeignKey("research_jobs.id", ondelete="CASCADE"), nullable=False)


class ResearchLease(Base):
    __tablename__ = "research_leases"
    job_id = Column(Integer, ForeignKey("research_jobs.id", ondelete="CASCADE"), primary_key=True)
    token = Column(String(64), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, nullable=False, default=1)

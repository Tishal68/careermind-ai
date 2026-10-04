from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from app.core.database import Base


class CareerProfile(Base):
    __tablename__ = "career_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    resume_session_id = Column(Integer, ForeignKey("resume_sessions.id", ondelete="CASCADE"), nullable=True)

    personal_info = Column(JSON, nullable=True)
    skills_matrix = Column(JSON, nullable=True)
    target_companies = Column(JSON, nullable=True)
    target_roles = Column(JSON, nullable=True)
    
    current_nex_score = Column(Float, default=89.0)
    current_ats_score = Column(Float, default=92.0)

    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    resume_session = relationship("ResumeSession")


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id = Column(Integer, primary_key=True, index=True)
    resume_session_id = Column(Integer, ForeignKey("resume_sessions.id", ondelete="CASCADE"), nullable=False)
    
    version_number = Column(Integer, default=1)
    file_name = Column(String(255), nullable=False)
    delta_summary = Column(JSON, nullable=True)
    ats_score_diff = Column(Float, default=0.0)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    resume_session = relationship("ResumeSession")

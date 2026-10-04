from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    target_job_role = Column(String(100), default="AI Engineer")
    preferred_ai_model = Column(String(100), default="gemini-2.5-flash")
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships with Cascade Delete
    resume_sessions = relationship("ResumeSession", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("CareerReport", back_populates="user", cascade="all, delete-orphan")
    career_memory = relationship("CareerMemory", back_populates="user", uselist=False, cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    interview_sessions = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan")

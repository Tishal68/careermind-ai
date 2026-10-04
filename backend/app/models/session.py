import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class ResumeSession(Base):
    __tablename__ = "resume_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_uuid = Column(String(64), default=lambda: str(uuid.uuid4()), index=True, nullable=False)
    
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_path = Column(String(512), nullable=False)
    raw_text = Column(Text, nullable=True)
    parsed_data = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Parent Entity Relationships with Cascade Delete
    user = relationship("User", back_populates="resume_sessions")
    reports = relationship("CareerReport", back_populates="resume_session", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="resume_session", cascade="all, delete-orphan")
    interview_sessions = relationship("InterviewSession", back_populates="resume_session", cascade="all, delete-orphan")

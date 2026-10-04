from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from app.core.database import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_session_id = Column(Integer, ForeignKey("resume_sessions.id", ondelete="CASCADE"), nullable=True)
    
    interview_type = Column(String(50), nullable=False)
    target_role = Column(String(100), nullable=False)
    overall_score = Column(Float, default=0.0)
    history = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="interview_sessions")
    resume_session = relationship("ResumeSession", back_populates="interview_sessions")

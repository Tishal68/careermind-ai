from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class CareerMemory(Base):
    __tablename__ = "career_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    target_job_role = Column(String(100), default="AI Engineer")
    extracted_skills = Column(JSON, default=list)
    mastered_skills = Column(JSON, default=list)
    skill_gaps = Column(JSON, default=list)
    completed_milestones = Column(JSON, default=list)
    interview_performance_summary = Column(JSON, default=dict)
    last_nex_score = Column(Integer, default=89)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="career_memory")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_session_id = Column(Integer, ForeignKey("resume_sessions.id", ondelete="CASCADE"), nullable=True)
    
    session_date = Column(String(20), nullable=False)
    title = Column(String(255), default="Daily AI Coaching Session")
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="chat_sessions")
    resume_session = relationship("ResumeSession", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="chat_session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    chat_session = relationship("ChatSession", back_populates="messages")

    @property
    def user_id(self) -> int:
        return self.chat_session.user_id if self.chat_session else 0

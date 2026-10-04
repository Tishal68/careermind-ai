from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from app.core.database import Base


class CareerReport(Base):
    __tablename__ = "career_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_session_id = Column(Integer, ForeignKey("resume_sessions.id", ondelete="CASCADE"), nullable=False)

    field = Column(String(100), nullable=False)
    job_role = Column(String(100), nullable=False)
    experience_level = Column(String(50), nullable=False)

    nex_score = Column(Float, default=78.5)
    nex_score_breakdown = Column(JSON, nullable=True)

    resume_score = Column(Float, default=80.0)
    ats_score = Column(Float, default=82.0)
    readiness_score = Column(Float, default=75.0)

    analysis_data = Column(JSON, nullable=True)
    gap_analysis = Column(JSON, nullable=True)
    roadmap_data = Column(JSON, nullable=True)
    project_recommendations = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="reports")
    resume_session = relationship("ResumeSession", back_populates="reports")

    @property
    def resume_id(self) -> int:
        return self.resume_session_id

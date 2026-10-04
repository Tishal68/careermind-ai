from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.session import ResumeSession
from app.models.report import CareerReport
from app.kernel.state import KernelState


class KernelManager:
    """Kernel State Manager acting as the UI-independent permanent source of truth."""

    def get_active_state(self, db: Session, user_id: int, user_name: str) -> KernelState:
        latest_session = db.query(ResumeSession).filter(ResumeSession.user_id == user_id).order_by(ResumeSession.created_at.desc()).first()
        latest_report = db.query(CareerReport).filter(CareerReport.user_id == user_id).order_by(CareerReport.created_at.desc()).first()

        if latest_session and latest_report:
            parsed = latest_session.parsed_data or {}
            skills = parsed.get("technical_skills", [])
            gap = latest_report.gap_analysis or {}

            return KernelState(
                user_id=user_id,
                session_id=latest_session.id,
                session_uuid=latest_session.session_uuid,
                target_job_role=latest_report.job_role,
                nex_score=latest_report.nex_score or 89.0,
                ats_score=latest_report.ats_score or 92.0,
                skills_match=78.0,
                interview_readiness=latest_report.readiness_score or 74.0,
                extracted_skills=skills,
                missing_skills=gap.get("missing_skills", []),
                roadmap_milestones=(latest_report.roadmap_data or {}).get("milestones", []),
                project_recommendations=latest_report.project_recommendations or []
            )

        return KernelState(
            user_id=user_id,
            target_job_role="AI Engineer",
            nex_score=0.0,
            ats_score=0.0,
            skills_match=0.0,
            interview_readiness=0.0,
            is_synchronized=False
        )


kernel_manager = KernelManager()

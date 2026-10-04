from typing import Dict, Any
from sqlalchemy.orm import Session
from app.ai.brain import ai_brain


class AICommandCenter:
    """Central AI Command Center Orchestrator executing Career OS Kernel & AI Brain."""

    def process_auto_pipeline(
        self,
        db: Session,
        user_id: int,
        user_name: str,
        target_role: str,
        parsed_resume: Dict[str, Any]
    ) -> Dict[str, Any]:
        return ai_brain.orchestrate_career_os(db, user_id, user_name, target_role, parsed_resume)


command_center = AICommandCenter()

from typing import Dict, Any, List


class WorkspaceEngine:
    """Central controller of active dashboard snapshot state."""

    def build_snapshot(
        self,
        user_name: str,
        target_role: str,
        nex_score: float,
        ats_score: float,
        skills_match: float,
        interview_readiness: float,
        top_priority_directive: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "greeting": f"Good morning, {user_name} 👋",
            "headline": "Your career is moving forward",
            "target_role": target_role,
            "nex_score": nex_score,
            "ats_score": ats_score,
            "skills_match": skills_match,
            "interview_readiness": interview_readiness,
            "top_priority": top_priority_directive,
            "is_synchronized": True
        }


workspace_engine = WorkspaceEngine()

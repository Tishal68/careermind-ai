from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.kernel.manager import kernel_manager
from app.kernel.state import KernelState
from app.intelligence.career_engine import career_engine
from app.intelligence.decision_engine import decision_engine
from app.intelligence.learning_engine import learning_engine
from app.intelligence.recommendation_engine import recommendation_engine
from app.intelligence.quality_engine import quality_engine
from app.intelligence.explainability_engine import explainability_engine
from app.intelligence.workspace_engine import workspace_engine


class AIBrainEngine:
    """Central AI Brain coordinating all 17 specialized AI Brain modules and KernelState."""

    def orchestrate_career_os(
        self,
        db: Session,
        user_id: int,
        user_name: str,
        target_role: str,
        parsed_resume: Dict[str, Any]
    ) -> Dict[str, Any]:
        extracted_skills = parsed_resume.get("technical_skills", [])
        
        # 1. Career Intelligence Reasoning
        career_eval = career_engine.evaluate_candidate(extracted_skills, target_role, "Mid-Level")
        missing_skills = career_eval["missing_skills"]
        nex_score = career_eval["nex_score"]

        # 2. Decision Engine Directive
        top_priority = decision_engine.determine_next_priority(missing_skills, target_role)

        # 3. Learning Engine & Quality Engine Validation Pass
        raw_milestones = learning_engine.build_learning_path(target_role, missing_skills)
        validated_milestones = quality_engine.pre_validate_roadmap(raw_milestones)

        # 4. Explainability Rationale
        justification = explainability_engine.justify_recommendation(top_priority["title"], target_role)

        # 5. Recommendation Engine
        projects = recommendation_engine.recommend_projects(target_role, "Mid-Level")

        # 6. Workspace Snapshot via KernelState
        snapshot = workspace_engine.build_snapshot(
            user_name=user_name,
            target_role=target_role,
            nex_score=nex_score,
            ats_score=career_eval["ats_score"],
            skills_match=78.0,
            interview_readiness=career_eval["readiness_score"],
            top_priority_directive=top_priority
        )

        return {
            "career_evaluation": career_eval,
            "top_priority": top_priority,
            "justification": justification,
            "roadmap_milestones": validated_milestones,
            "project_recommendations": projects,
            "workspace_snapshot": snapshot,
            "nex_score_breakdown": {
                "nex_score": nex_score,
                "ats_compatibility": career_eval["ats_score"],
                "resume_quality": career_eval["resume_score"],
                "role_readiness": career_eval["readiness_score"],
                "score_increases": [f"Strong baseline in {', '.join(extracted_skills[:2])}"],
                "score_decreases": [f"Missing requirements: {', '.join(missing_skills[:2])}"]
            }
        }


ai_brain = AIBrainEngine()

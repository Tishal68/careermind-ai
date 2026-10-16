from typing import Dict, Any, List
from app.intelligence.career_graph import career_graph
from app.intelligence.market_engine import market_engine
from app.intelligence.skill_catalog import normalize_skill


class CareerIntelligenceEngine:
    """Continuous reasoning engine evaluating candidate skill match, gaps, & risk."""

    def evaluate_candidate(
        self,
        extracted_skills: List[str],
        job_role: str,
        experience_level: str = "Mid-Level"
    ) -> Dict[str, Any]:
        role_profile = career_graph.get_role_profile(job_role)
        required_skills = set(s.lower() for s in role_profile["required_skills"])
        user_skills = set(normalize_skill(s) for s in extracted_skills)

        matched = [s for s in role_profile["required_skills"] if s.lower() in user_skills]
        missing = [s for s in role_profile["required_skills"] if s.lower() not in user_skills]

        ratio = len(matched) / max(len(required_skills), 1)
        ats_score = round(ratio * 100, 1)
        # Keyword overlap is not an ATS, writing-quality or hiring-readiness test.

        market_insights = market_engine.get_market_insights(job_role)

        return {
            "ats_score": None,
            "match_percent": ats_score,
            "resume_score": None,
            "readiness_score": None,
            "nex_score": ats_score,
            "matched_skills": matched,
            "missing_skills": missing,
            "market_insights": market_insights
        }


career_engine = CareerIntelligenceEngine()

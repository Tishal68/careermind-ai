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
        qual_score = round(min(100.0, max(60.0, len(extracted_skills) * 4.0 + 50.0)), 1)
        readiness_score = round(ats_score * 0.5 + qual_score * 0.5, 1)

        market_insights = market_engine.get_market_insights(job_role)

        return {
            "ats_score": ats_score,
            "match_percent": ats_score,
            "resume_score": qual_score,
            "readiness_score": readiness_score,
            "nex_score": round(ats_score * 0.4 + qual_score * 0.3 + readiness_score * 0.3, 1),
            "matched_skills": matched,
            "missing_skills": missing,
            "market_insights": market_insights
        }


career_engine = CareerIntelligenceEngine()

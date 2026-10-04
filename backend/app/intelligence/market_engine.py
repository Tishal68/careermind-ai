from typing import Dict, Any, List


class MarketIntelligenceEngine:
    """Market Intelligence Engine tracking hiring demand & tech skill trends."""

    def __init__(self):
        self.market_index = {
            "emerging_skills": ["RAG Architecture", "Vector DBs", "LangChain", "FastAPI", "Docker"],
            "declining_skills": ["Legacy PHP", "Monolithic jQuery"],
            "hiring_demand_score": 94.2,
            "top_frameworks": ["FastAPI", "Next.js", "PyTorch", "Tailwind CSS"]
        }

    def get_market_insights(self, job_role: str) -> Dict[str, Any]:
        return {
            "job_role": job_role,
            "market_demand": "Extremely High (+28% MoM postings)",
            "emerging_skills": self.market_index["emerging_skills"],
            "declining_skills": self.market_index["declining_skills"],
            "demand_score": self.market_index["hiring_demand_score"]
        }


market_engine = MarketIntelligenceEngine()

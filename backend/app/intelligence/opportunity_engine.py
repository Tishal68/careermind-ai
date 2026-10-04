from typing import Dict, Any, List


class OpportunityEngine:
    """Opportunity Engine matching hackathons, internships, & open source programs."""

    def match_opportunities(self, target_role: str) -> List[Dict[str, Any]]:
        return [
            {
                "id": "opp_1",
                "title": "Global AI Hackathon 2026",
                "category": "Hackathon",
                "relevance_reason": f"Focuses on RAG & Agentic Systems tailored for {target_role} candidates.",
                "deadline": "14 Days"
            },
            {
                "id": "opp_2",
                "title": "FastAPI Core Contributor Sprint",
                "category": "Open Source",
                "relevance_reason": "High-impact repository contribution to boost GitHub portfolio visibility.",
                "deadline": "Ongoing"
            }
        ]


opportunity_engine = OpportunityEngine()

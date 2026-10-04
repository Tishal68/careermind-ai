from typing import Dict, Any, List


class CompanyIntelligenceEngine:
    """Company Intelligence Engine profiling Tier-1 tech company hiring bars."""

    def __init__(self):
        self.tier1_companies = {
            "google": {"interview_focus": "Algorithms, System Design, Python/C++", "culture_bar": "Googliness & Leadership"},
            "meta": {"interview_focus": "System Design, Microservices, PyTorch", "culture_bar": "Move Fast & Build"},
            "amazon": {"interview_focus": "AWS Architecture, Distributed Systems", "culture_bar": "16 Leadership Principles"},
            "microsoft": {"interview_focus": "Azure, Cloud Architecture, C#/.NET", "culture_bar": "Growth Mindset"},
            "openai": {"interview_focus": "LLM Fine-tuning, MLOps, Vector Indexing", "culture_bar": "Research to Production Velocity"}
        }

    def get_company_profile(self, company_name: str) -> Dict[str, Any]:
        return self.tier1_companies.get(company_name.lower(), {
            "interview_focus": "System Architecture & End-to-End Execution",
            "culture_bar": "High Ownership & Autonomous Output"
        })


company_engine = CompanyIntelligenceEngine()

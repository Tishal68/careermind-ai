from typing import Dict, Any, List


class CareerGraphEngine:
    """Career Graph Engine mapping job roles, core expectations, & salary benchmarks."""

    def __init__(self):
        self.roles: Dict[str, Dict[str, Any]] = {
            "ai engineer": {
                "required_skills": ["Python", "FastAPI", "PyTorch", "RAG", "Vector Databases", "Docker"],
                "salary_range": "$135,000 - $185,000",
                "career_growth_velocity": "Very High",
                "target_level": "Mid-Level"
            },
            "machine learning engineer": {
                "required_skills": ["Python", "Scikit-Learn", "Pandas", "Docker", "MLOps", "SQL"],
                "salary_range": "$130,000 - $175,000",
                "career_growth_velocity": "High",
                "target_level": "Mid-Level"
            },
            "data scientist": {
                "required_skills": ["Python", "SQL", "Pandas", "Statistics", "Data Analysis", "Tableau"],
                "salary_range": "$120,000 - $160,000",
                "career_growth_velocity": "High",
                "target_level": "Mid-Level"
            }
        }

    def get_role_profile(self, job_role: str) -> Dict[str, Any]:
        return self.roles.get(job_role.lower(), {
            "required_skills": ["Python", "Git", "SQL", "Docker", "REST API"],
            "salary_range": "$115,000 - $155,000",
            "career_growth_velocity": "Moderate",
            "target_level": "Mid-Level"
        })


career_graph = CareerGraphEngine()

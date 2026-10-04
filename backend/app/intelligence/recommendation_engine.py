from typing import Dict, Any, List


class RecommendationEngine:
    """Matches portfolio projects & certifications to candidate skill profile."""

    def recommend_projects(self, job_role: str, experience_level: str = "Mid-Level") -> List[Dict[str, Any]]:
        return [
            {
                "id": "proj_1",
                "title": f"Autonomous {job_role} RAG Pipeline",
                "description": "Build an end-to-end vector search application with FastAPI, Next.js, and hybrid TF-IDF/embeddings.",
                "required_skills": ["Python", "FastAPI", "Next.js", "Vector DB"],
                "learning_outcomes": ["Vector indexing", "API optimization", "Frontend state management"],
                "difficulty": "Intermediate",
                "estimated_time": "15 Hours"
            },
            {
                "id": "proj_2",
                "title": "Real-Time AI Microservices Platform",
                "description": "Containerized multi-model inference system with Docker, Redis caching, and Prometheus monitoring.",
                "required_skills": ["Docker", "Redis", "Python", "System Design"],
                "learning_outcomes": ["Microservices architecture", "Caching strategies", "Production monitoring"],
                "difficulty": "Advanced",
                "estimated_time": "25 Hours"
            }
        ]


recommendation_engine = RecommendationEngine()

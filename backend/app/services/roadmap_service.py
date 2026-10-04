from typing import Dict, Any, List


class RoadmapService:
    @staticmethod
    def generate_roadmap(job_role: str, missing_skills: List[str]) -> List[Dict[str, Any]]:
        missing = missing_skills if missing_skills else ["Advanced System Architecture", "Deployment Optimization"]
        
        milestones = []
        topics = [
            ("Foundation & Core Principles", missing[0] if len(missing) > 0 else "Core Principles"),
            ("Deep Dive & Frameworks", missing[1] if len(missing) > 1 else "Frameworks"),
            ("System Integration & Projects", missing[2] if len(missing) > 2 else "System Integration"),
            ("Interview Mastery & Production Prep", "Production Deployment & Monitoring")
        ]

        for week_idx, (title, topic) in enumerate(topics, start=1):
            milestones.append({
                "week_number": week_idx,
                "title": title,
                "focus_topic": topic,
                "resources": [
                    f"Official {topic} Documentation",
                    f"Interactive Code Tutorial for {job_role}"
                ],
                "tasks": [
                    {"id": f"w{week_idx}_t1", "task_name": f"Study key concepts of {topic}", "is_completed": False},
                    {"id": f"w{week_idx}_t2", "task_name": f"Implement a mini project using {topic}", "is_completed": False},
                    {"id": f"w{week_idx}_t3", "task_name": f"Review interview questions for {topic}", "is_completed": False}
                ],
                "estimated_hours": 12
            })

        return milestones

    @staticmethod
    def get_project_recommendations(job_role: str, experience_level: str) -> List[Dict[str, Any]]:
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

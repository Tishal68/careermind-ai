from typing import Dict, Any, List
from app.intelligence.knowledge_graph import knowledge_graph


class LearningEngine:
    """Generates structured 4-week learning paths, schedules, & capstone projects."""

    def build_learning_path(self, job_role: str, missing_skills: List[str]) -> List[Dict[str, Any]]:
        gaps = missing_skills if missing_skills else ["System Design", "Docker", "RAG Pipeline"]
        milestones = []

        topics = [
            ("Foundation & Core Principles", gaps[0] if len(gaps) > 0 else "Core Architecture"),
            ("Framework Deep Dive", gaps[1] if len(gaps) > 1 else "Frameworks"),
            ("System Integration & Mini-Projects", gaps[2] if len(gaps) > 2 else "Microservices"),
            ("Production Mastery & Capstone", "Production Deployment")
        ]

        for week_idx, (title, topic) in enumerate(topics, start=1):
            prereqs = knowledge_graph.get_prerequisites(topic)
            milestones.append({
                "week_number": week_idx,
                "title": title,
                "focus_topic": topic,
                "prerequisites": prereqs,
                "resources": [
                    f"Official {topic} Documentation",
                    f"Interactive Tutorial for {job_role}"
                ],
                "tasks": [
                    {"id": f"w{week_idx}_t1", "task_name": f"Study key concepts of {topic}", "is_completed": False},
                    {"id": f"w{week_idx}_t2", "task_name": f"Implement a mini project using {topic}", "is_completed": False},
                    {"id": f"w{week_idx}_t3", "task_name": f"Review interview questions for {topic}", "is_completed": False}
                ],
                "estimated_hours": 12
            })

        return milestones


learning_engine = LearningEngine()

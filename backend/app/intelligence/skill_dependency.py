from typing import List, Dict, Any
from app.intelligence.knowledge_graph import knowledge_graph


class SkillDependencyEngine:
    """Skill Dependency Engine validating prerequisites & preventing invalid learning order."""

    def validate_learning_sequence(self, topics: List[str]) -> List[str]:
        validated = []
        for topic in topics:
            prereqs = knowledge_graph.get_prerequisites(topic)
            # Ensure prerequisites appear before dependent topic
            for p in prereqs:
                if p not in [t.lower() for t in validated] and p not in [t.lower() for t in topics]:
                    validated.append(p.title())
            if topic not in validated:
                validated.append(topic)
        return validated


skill_dependency_engine = SkillDependencyEngine()

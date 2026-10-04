from typing import List, Dict, Any


class KnowledgeGraphEngine:
    """Skill Knowledge Graph representing technology dependencies & prerequisite trees."""
    
    def __init__(self):
        self.graph: Dict[str, Dict[str, Any]] = {
            "python": {
                "prerequisites": [],
                "next_steps": ["fastapi", "pandas", "pytorch", "scikit-learn"],
                "category": "language"
            },
            "fastapi": {
                "prerequisites": ["python", "rest api"],
                "next_steps": ["docker", "vector databases", "microservices"],
                "category": "backend"
            },
            "docker": {
                "prerequisites": ["linux"],
                "next_steps": ["kubernetes", "ci/cd", "aws"],
                "category": "devops"
            },
            "vector databases": {
                "prerequisites": ["python", "fastapi"],
                "next_steps": ["rag", "langchain"],
                "category": "ai_infrastructure"
            },
            "rag": {
                "prerequisites": ["vector databases", "fastapi", "python"],
                "next_steps": ["generative ai engineer", "production ai"],
                "category": "ai_architecture"
            },
            "system design": {
                "prerequisites": ["rest api", "sql", "fastapi"],
                "next_steps": ["microservices", "aws", "kubernetes"],
                "category": "architecture"
            }
        }

    def get_prerequisites(self, skill: str) -> List[str]:
        node = self.graph.get(skill.lower())
        return node["prerequisites"] if node else []

    def get_next_skills(self, skill: str) -> List[str]:
        node = self.graph.get(skill.lower())
        return node["next_steps"] if node else []


knowledge_graph = KnowledgeGraphEngine()

from typing import Optional
from app.ai.providers.router import ai_router_engine
from app.ai.prompts.coach_prompts import SYSTEM_COACH_PROMPT, USER_COACH_TEMPLATE


class CoachAgent:
    def __init__(self):
        self.router = ai_router_engine

    def execute_coaching(
        self,
        query: str,
        target_role: str,
        skills: list,
        nex_score: int = 89,
        provider_name: Optional[str] = None
    ) -> str:
        prompt = USER_COACH_TEMPLATE.format(
            target_role=target_role,
            skills=", ".join(skills) if skills else "Software Engineering",
            nex_score=nex_score,
            query=query
        )
        response = self.router.generate_text(prompt, system_prompt=SYSTEM_COACH_PROMPT, provider_name=provider_name)
        if response:
            return response

        # Intelligent Fallback
        q_lower = query.lower().strip()
        if q_lower in ["hi", "hello", "hey"]:
            return f"Good day! 👋 I've synchronized your career memory for {target_role}. What milestone should we tackle today?"
        elif "roadmap" in q_lower or "learn" in q_lower:
            return f"To accelerate your preparation for {target_role}: 1) Master System Design & Microservices, 2) Build containerized APIs with FastAPI & Docker, 3) Complete mock interview questions."
        else:
            return f"Regarding '{query}': Continue executing your 4-week action plan items to raise your NexScore™!"


coach_agent = CoachAgent()

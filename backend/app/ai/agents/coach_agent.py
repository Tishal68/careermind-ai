from fastapi import HTTPException
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
        nex_score: Optional[float] = None,
        provider_name: Optional[str] = None,
        context: str = ""
    ) -> str:
        prompt = USER_COACH_TEMPLATE.format(
            target_role=target_role,
            skills=", ".join(skills) if skills else "No skills identified",
            nex_score=nex_score,
            context=context,
            query=query
        )
        response = self.router.generate_text(prompt, system_prompt=SYSTEM_COACH_PROMPT, provider_name=provider_name)
        if response:
            return response

        raise HTTPException(status_code=503, detail="Ollama returned an empty reply. Please try again.")


coach_agent = CoachAgent()

import logging
from typing import Dict, Any, List
from app.services.gemini_service import call_gemini_api

logger = logging.getLogger(__name__)


class RAGAssistantService:
    @staticmethod
    def generate_chat_response(query: str, chat_history: List[Dict[str, Any]], parsed_resume: Dict[str, Any] = None) -> str:
        resume_context = f"Candidate Skills: {', '.join(parsed_resume.get('technical_skills', []))}" if parsed_resume else ""
        gemini_prompt = f"""
Act as NexPath Executive AI Career Coach. Answer the candidate's career question directly, providing actionable, professional, and clear advice.
Candidate Question: {query}
{resume_context}
"""
        response_text = call_gemini_api(gemini_prompt)
        if response_text:
            return response_text

        q_lower = query.lower().strip()
        if q_lower in ["hi", "hello", "hey", "greetings", "hi there"]:
            return "Hello! 👋 I am your NexPath AI Assistant. How can I help analyze your resume, identify skill gaps, or prepare for mock interviews today?"

        if "roadmap" in q_lower or "learn" in q_lower or "skill" in q_lower:
            return "To accelerate your learning roadmap for AI & Software Engineering: 1) Master Python & FastAPI backend microservices, 2) Study RAG vector architectures & embeddings, and 3) Build containerized full-stack projects using Next.js & Docker."
        elif "interview" in q_lower or "prepare" in q_lower or "question" in q_lower:
            return "For technical and behavioral interview preparation: Use the STAR method (Situation, Task, Action, Result) for behavioral questions, and quantify system performance trade-offs for technical questions."
        elif "resume" in q_lower or "ats" in q_lower or "score" in q_lower:
            return "To optimize your ATS resume score: Ensure clean single-column PDF formatting, use clear standard section headings, and start every bullet point with a strong action verb."
        else:
            return f"Regarding '{query}': Prioritize building hands-on portfolio projects, mastering core software architecture principles, and tailoring your resume to highlight relevant technical accomplishments!"

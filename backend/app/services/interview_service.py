import json
import logging
from typing import Dict, Any
from app.services.gemini_service import call_gemini_api

logger = logging.getLogger(__name__)

DEFAULT_QUESTIONS = {
    "Technical": [
        "Explain how vector embeddings and cosine similarity enable semantic search in RAG pipelines.",
        "How do you handle rate limits and API retries in production microservices?",
        "Compare SQL vs NoSQL indexing strategy when handling millions of queries per second."
    ],
    "Behavioral": [
        "Describe a situation where a technical project deadline was threatened and how you adapted.",
        "Tell me about a time you disagreed with a senior engineer's architecture decision and how you resolved it."
    ],
    "HR": [
        "Why do you want to join our engineering team, and where do you see yourself in 3 years?",
        "What are your core salary expectations and preferred work culture environment?"
    ],
    "Mixed": [
        "Explain a complex technical project you built recently and the key business outcome achieved."
    ]
}


class InterviewService:
    @staticmethod
    def generate_initial_question(interview_type: str, target_role: str) -> str:
        prompt = f"Generate 1 challenging {interview_type} technical interview question for a {target_role} position. Return ONLY the question string."
        gemini_q = call_gemini_api(prompt)
        if gemini_q:
            return f"[{target_role} - {interview_type}] {gemini_q}"

        questions = DEFAULT_QUESTIONS.get(interview_type, DEFAULT_QUESTIONS["Technical"])
        return f"[{target_role} - {interview_type} Question] {questions[0]}"

    @staticmethod
    def evaluate_response(interview_type: str, target_role: str, question: str, user_answer: str) -> Dict[str, Any]:
        prompt = f"""
Act as a Tech Lead interviewing a candidate for a {target_role} position.
Question Asked: {question}
Candidate Answer: {user_answer}

Evaluate the candidate answer and return ONLY a valid JSON object matching this schema:
{{
  "score": <float between 50 and 100>,
  "strengths": [<array of 1-2 strength strings>],
  "mistakes": [<array of 1-2 area of improvement strings>],
  "suggested_answer": "<top-tier model answer>",
  "next_question": "<follow up interview question>"
}}
"""
        raw = call_gemini_api(prompt)
        if raw:
            try:
                json_str = raw.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()
                res = json.loads(json_str)
                return {
                    "score": float(res.get("score", 88.0)),
                    "strengths": res.get("strengths", ["Clear explanation of core technical concepts."]),
                    "mistakes": res.get("mistakes", ["Could elaborate on system scaling trade-offs."]),
                    "suggested_answer": res.get("suggested_answer", "A top-tier answer highlights architectural trade-offs and real-world metrics."),
                    "next_question": res.get("next_question", "Follow-up: How would you optimize query throughput under 10x traffic spikes?")
                }
            except Exception as e:
                logger.warning(f"Failed to parse Gemini interview evaluation: {e}")

        ans_len = len(user_answer.strip())
        score = min(95.0, max(65.0, ans_len * 0.3 + 60.0))
        return {
            "score": round(score, 1),
            "strengths": ["Clear explanation of technical concepts.", "Demonstrated hands-on experience."],
            "mistakes": ["Could include more specific performance metrics or trade-off analysis."],
            "suggested_answer": "A top-tier answer emphasizes architectural trade-offs, scalability considerations, and real-world business impact.",
            "next_question": f"Follow-up: How would you optimize this system if query traffic scaled by 10x?"
        }

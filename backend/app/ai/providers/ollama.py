import os
import json
import logging
from typing import Optional, Dict, Any
import httpx
from app.core.config import settings
from app.ai.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)

# Strict Guardrail System Prompt restricting the LLM to only NexPath career counseling
STRICT_CAREER_GUARDRAIL = """
You are NexPath AI Career Operating System Mentor & Coach.
CRITICAL MANDATE:
1. You MUST ONLY answer questions related to careers, software engineering, resumes, ATS optimization, skill gaps, learning roadmaps, coding projects, system design, mock interviews, tech industries, and professional career growth.
2. If a user asks about ANYTHING ELSE (e.g. general chit-chat, cooking, politics, pop culture, creative fiction, general trivia, math homework, recipes, jokes, or non-career topics), you MUST POLITELY REFUSE with:
"I am dedicated exclusively to your career growth as your NexPath Career Operating System. Please ask me about your resume, skill gaps, learning roadmap, portfolio projects, or technical interview preparation."
3. Never break character. Never answer off-topic queries under any circumstances.
"""


class OllamaLLMProvider(BaseLLMProvider):
    """
    Ollama LLM Provider with strict domain boundary enforcement for NexPath.
    Connects to Ollama API (default: http://127.0.0.1:11434).
    Uses installed model (e.g., llama3.2, deepseek-r1:8b).
    """

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.timeout = 120.0

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        combined_system = f"{STRICT_CAREER_GUARDRAIL}\n\n{system_prompt or ''}".strip()
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": combined_system,
            "stream": False,
            "keep_alive": "30m",
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
                "num_ctx": 2048,
                "num_predict": 250
            }
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    response_text = data.get("response", "").strip()
                    if response_text:
                        return response_text
                else:
                    logger.warning(f"Ollama API returned status {res.status_code}: {res.text}")
        except Exception as e:
            logger.warning(f"Ollama connection error on {url}: {e}")

        return ""

    def generate_json(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        json_instruction = (
            "\n\nYou must respond STRICTLY with a valid JSON object matching the requested schema. "
            "Do not include any explanation, markdown formatting, or preamble."
        )
        text_out = self.generate_text(f"{prompt}{json_instruction}")
        if not text_out:
            return {}

        try:
            cleaned = text_out.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            return json.loads(cleaned)
        except Exception as e:
            logger.warning(f"Ollama JSON parse error: {e}")
            return {}

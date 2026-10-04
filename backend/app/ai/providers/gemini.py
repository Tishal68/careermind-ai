import os
import json
import logging
from typing import Optional, Dict, Any
from google import genai
from app.core.config import settings
from app.ai.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GeminiLLMProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key or not self.api_key.startswith("AIzaSy"):
            return ""
        try:
            client = genai.Client(api_key=self.api_key)
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            for model_name in ["gemini-1.5-flash", "gemini-2.0-flash", settings.GEMINI_MODEL]:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=full_prompt,
                    )
                    if response and response.text:
                        return response.text.strip()
                except Exception as inner_e:
                    logger.warning(f"Gemini model {model_name} warning: {inner_e}")
                    continue
        except Exception as e:
            logger.error(f"Gemini API Provider error: {e}")
        return ""

    def generate_json(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        text_out = self.generate_text(prompt)
        if not text_out:
            return {}
        try:
            json_str = text_out.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Gemini JSON parse warning: {e}")
            return {}

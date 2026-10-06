import json
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import httpx
from fastapi import HTTPException
from app.core.config import settings
from app.ai.providers.base import BaseLLMProvider
from app.ai.prompts.coach_prompts import STRICT_CAREER_GUARDRAIL


class OllamaLLMProvider(BaseLLMProvider):
    """Local or hosted Ollama inference with optional server-side authentication."""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.api_key = api_key if api_key is not None else settings.OLLAMA_API_KEY.get_secret_value()
        self.timeout = 180.0
        self.num_predict = 384
        self.num_ctx = 8192

    def _generate(self, prompt: str, system_prompt: Optional[str] = None, output_format=None) -> str:
        system = system_prompt or ""
        if STRICT_CAREER_GUARDRAIL not in system:
            system = f"{STRICT_CAREER_GUARDRAIL}\n{system}"
        payload = {
            "model": self.model,
            "stream": False,
            "keep_alive": "30m",
            "options": {"temperature": 0.2, "top_p": 0.9,
                        "num_ctx": max(self.num_ctx, 32768 if len(prompt) > 20000 else 8192),
                        "num_predict": self.num_predict},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        if output_format is not None:
            payload["format"] = output_format
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            response = httpx.post(f"{self.base_url}/api/chat", json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            content = response.json()["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("Empty Ollama reply")
            return content.strip()
        except httpx.TimeoutException as exc:
            raise HTTPException(status_code=503, detail="Ollama took too long to respond. Try a faster model or a shorter job description, then retry.") from exc
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            if code in (401, 403):
                detail = "Ollama authentication failed. Check OLLAMA_API_KEY in the backend environment."
            elif code == 404:
                detail = "Ollama endpoint or model was not found. Check OLLAMA_BASE_URL and OLLAMA_MODEL."
            elif code == 429:
                detail = "Ollama usage limit reached. Check your account limits or try again later."
            else:
                detail = "The Ollama server could not complete the request. Please try again."
            raise HTTPException(status_code=503, detail=detail) from exc
        except (httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
            raise HTTPException(status_code=503, detail="Ollama is unreachable or returned an invalid reply. Check the configured server address and model, then retry.") from exc

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        return self._generate(prompt, system_prompt)

    def generate_json(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cloud = urlparse(self.base_url).hostname == "ollama.com"
        instruction = "\nRespond with only a valid JSON object, without Markdown."
        if schema:
            instruction += "\nRequired JSON schema: " + json.dumps(schema)
        text = self._generate(prompt + instruction, output_format=None if cloud else schema or "json")
        if text.startswith("```") and text.endswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        try:
            result = json.loads(text)
            if not isinstance(result, dict):
                raise ValueError("Expected an object")
            return result
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=502, detail="Ollama did not return a valid JSON object.") from exc

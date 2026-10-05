from typing import Optional, Dict, Any
from fastapi import HTTPException
from app.core.config import settings
from app.ai.providers.base import BaseLLMProvider
from app.ai.providers.gemini import GeminiLLMProvider
from app.ai.providers.ollama import OllamaLLMProvider


class AIProviderRouter:
    def __init__(self):
        self.ollama = OllamaLLMProvider()
        self.gemini = GeminiLLMProvider()
        self.default_name = settings.DEFAULT_AI_PROVIDER.lower()

    def get_provider(self, provider_name: Optional[str] = None) -> BaseLLMProvider:
        target = (provider_name or self.default_name).lower()
        if target == "gemini":
            return self.gemini
        return self.ollama

    def _generate(self, method: str, provider_name: Optional[str], *args):
        provider = self.get_provider(provider_name)
        try:
            result = getattr(provider, method)(*args)
        except HTTPException as exc:
            if not settings.AI_FALLBACK_ENABLED or exc.status_code not in (502, 503):
                raise
            result = None
        if not result and settings.AI_FALLBACK_ENABLED:
            alternate = self.gemini if provider is self.ollama else self.ollama
            result = getattr(alternate, method)(*args)
        if not result:
            raise HTTPException(status_code=503, detail="The selected AI provider could not produce a reply. Check its configuration and try again.")
        return result

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, provider_name: Optional[str] = None) -> str:
        return self._generate("generate_text", provider_name, prompt, system_prompt)

    def generate_json(self, prompt: str, schema: Optional[Dict[str, Any]] = None, provider_name: Optional[str] = None) -> Dict[str, Any]:
        return self._generate("generate_json", provider_name, prompt, schema)


ai_router_engine = AIProviderRouter()

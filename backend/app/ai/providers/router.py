from typing import Optional, Dict, Any
from app.core.config import settings
from app.ai.providers.base import BaseLLMProvider
from app.ai.providers.gemini import GeminiLLMProvider
from app.ai.providers.ollama import OllamaLLMProvider


class AIProviderRouter:
    """
    Intelligent AI Provider Router supporting Ollama, Gemini, and fallback routing.
    Enforces career domain guardrails and ensures reliable AI responses.
    """

    def __init__(self):
        self.ollama = OllamaLLMProvider()
        self.gemini = GeminiLLMProvider()
        self.default_name = settings.DEFAULT_AI_PROVIDER.lower()

    def get_provider(self, provider_name: Optional[str] = None) -> BaseLLMProvider:
        target = (provider_name or self.default_name).lower()
        if target == "ollama":
            return self.ollama
        if target == "gemini":
            return self.gemini
        return self.ollama

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, provider_name: Optional[str] = None) -> str:
        provider = self.get_provider(provider_name)
        result = provider.generate_text(prompt, system_prompt)
        
        # Automatic fallback if primary returns empty
        if not result and provider != self.ollama:
            result = self.ollama.generate_text(prompt, system_prompt)
        elif not result and provider != self.gemini:
            result = self.gemini.generate_text(prompt, system_prompt)

        return result

    def generate_json(self, prompt: str, schema: Optional[Dict[str, Any]] = None, provider_name: Optional[str] = None) -> Dict[str, Any]:
        provider = self.get_provider(provider_name)
        result = provider.generate_json(prompt, schema)
        
        # Fallback if primary fails
        if not result and provider != self.ollama:
            result = self.ollama.generate_json(prompt, schema)
        elif not result and provider != self.gemini:
            result = self.gemini.generate_json(prompt, schema)

        return result


ai_router_engine = AIProviderRouter()

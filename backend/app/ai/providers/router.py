from typing import Optional, Dict, Any
from app.ai.providers.base import BaseLLMProvider
from app.ai.providers.gemini import GeminiLLMProvider


class AIProviderRouter:
    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {
            "gemini": GeminiLLMProvider(),
            "default": GeminiLLMProvider()
        }

    def get_provider(self, provider_name: str = "gemini") -> BaseLLMProvider:
        return self.providers.get(provider_name.lower(), self.providers["default"])

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, provider_name: str = "gemini") -> str:
        provider = self.get_provider(provider_name)
        return provider.generate_text(prompt, system_prompt)

    def generate_json(self, prompt: str, schema: Optional[Dict[str, Any]] = None, provider_name: str = "gemini") -> Dict[str, Any]:
        provider = self.get_provider(provider_name)
        return provider.generate_json(prompt, schema)


ai_router_engine = AIProviderRouter()

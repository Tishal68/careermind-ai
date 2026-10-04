from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate raw text response from LLM provider."""
        pass

    @abstractmethod
    def generate_json(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate structured JSON response matching schema."""
        pass

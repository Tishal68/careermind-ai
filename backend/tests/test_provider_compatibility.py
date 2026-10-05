from unittest.mock import Mock

import httpx
import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.ai.providers.ollama import OllamaLLMProvider
from app.ai.providers.router import AIProviderRouter
from app.ai.prompts.coach_prompts import STRICT_CAREER_GUARDRAIL
from app.services.rag_service import RAGAssistantService


def test_configured_default_and_explicit_selection(monkeypatch):
    monkeypatch.setattr(settings, "DEFAULT_AI_PROVIDER", "gemini")
    router = AIProviderRouter()
    assert router.get_provider() is router.gemini
    assert router.get_provider("ollama") is router.ollama


@pytest.mark.parametrize("failure", ["", HTTPException(503, "Ollama offline")])
def test_no_implicit_cloud_fallback(monkeypatch, failure):
    monkeypatch.setattr(settings, "AI_FALLBACK_ENABLED", False)
    router = AIProviderRouter()
    router.ollama.generate_text = Mock(side_effect=failure) if isinstance(failure, Exception) else Mock(return_value=failure)
    router.gemini.generate_text = Mock(return_value="Cloud reply")
    with pytest.raises(HTTPException) as error:
        router.generate_text("Private resume context", provider_name="ollama")
    assert error.value.status_code == 503
    router.gemini.generate_text.assert_not_called()


def test_fallback_is_available_when_explicitly_enabled(monkeypatch):
    monkeypatch.setattr(settings, "AI_FALLBACK_ENABLED", True)
    router = AIProviderRouter()
    router.ollama.generate_text = Mock(side_effect=HTTPException(503, "offline"))
    router.gemini.generate_text = Mock(return_value="Career guidance")
    assert router.generate_text("Plan my career", provider_name="ollama") == "Career guidance"


def test_json_mode_custom_settings_and_guardrails(monkeypatch):
    def post(url, **kwargs):
        assert url == "http://localhost:11435/api/chat"
        payload = kwargs["json"]
        assert payload["model"] == "test-model"
        assert payload["format"] == {"type": "object"}
        assert STRICT_CAREER_GUARDRAIL in payload["messages"][0]["content"]
        assert kwargs["timeout"] > 30
        return httpx.Response(200, json={"message": {"content": '{"next_skill":"Python"}'}}, request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "post", post)
    provider = OllamaLLMProvider(base_url="http://localhost:11435/", model="test-model")
    assert provider.generate_json("Next skill", {"type": "object"}) == {"next_skill": "Python"}


@pytest.mark.parametrize("content", ["", None, "not JSON", "[]"])
def test_invalid_model_outputs_fail_explicitly(monkeypatch, content):
    monkeypatch.setattr(httpx, "post", lambda url, **kwargs: httpx.Response(
        200, json={"message": {"content": content}}, request=httpx.Request("POST", url)
    ))
    with pytest.raises(HTTPException) as error:
        OllamaLLMProvider().generate_json("Next skill")
    assert error.value.status_code in (502, 503)


def test_new_rag_path_uses_ollama_and_domain_instructions(monkeypatch):
    def post(url, **kwargs):
        system, prompt = kwargs["json"]["messages"]
        assert "career" in system["content"].lower()
        assert "Python" in prompt["content"]
        return httpx.Response(200, json={"message": {"content": "Practice Python APIs."}}, request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "post", post)
    assert RAGAssistantService.generate_chat_response("What should I learn?", [], {"technical_skills": ["Python"]}) == "Practice Python APIs."

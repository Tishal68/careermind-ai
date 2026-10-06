from unittest.mock import Mock

import httpx
import pytest
from fastapi import HTTPException
from pydantic import SecretStr

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


def test_cloud_key_sent_only_in_backend_authorization_header(monkeypatch):
    monkeypatch.setattr(settings, "OLLAMA_API_KEY", SecretStr("test-cloud-secret"))
    def post(url, **kwargs):
        assert url == "https://ollama.com/api/chat"
        assert kwargs["headers"] == {"Authorization": "Bearer test-cloud-secret"}
        assert "test-cloud-secret" not in str(kwargs["json"])
        assert kwargs["json"]["model"] == "gemma4:31b"
        return httpx.Response(200, json={"message": {"content": "Focus on Python."}}, request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "post", post)
    provider = OllamaLLMProvider(base_url="https://ollama.com", model="gemma4:31b")
    assert provider.generate_text("What skill should I learn?") == "Focus on Python."


def test_local_ollama_does_not_require_key(monkeypatch):
    def post(url, **kwargs):
        assert kwargs["headers"] == {}
        return httpx.Response(200, json={"message": {"content": "Learn Python."}}, request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "post", post)
    assert OllamaLLMProvider(api_key="").generate_text("Career advice") == "Learn Python."


@pytest.mark.parametrize("status,setting", [(401, "OLLAMA_API_KEY"), (403, "OLLAMA_API_KEY"), (404, "OLLAMA_MODEL"), (429, "usage limit")])
def test_cloud_errors_are_actionable_without_exposing_key(monkeypatch, status, setting):
    monkeypatch.setattr(httpx, "post", lambda url, **kwargs: httpx.Response(
        status, json={"error": "private upstream diagnostic"}, request=httpx.Request("POST", url)
    ))
    with pytest.raises(HTTPException) as error:
        OllamaLLMProvider(api_key="test-cloud-secret").generate_text("Career advice")
    assert setting in error.value.detail
    assert "test-cloud-secret" not in error.value.detail
    assert "private upstream diagnostic" not in error.value.detail

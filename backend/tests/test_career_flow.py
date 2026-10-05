from io import BytesIO
from unittest.mock import Mock

import docx
import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.session import ResumeSession
from app.api.v1 import resume, reports, coach
from app.intelligence.career_graph import career_graph
from app.intelligence.career_engine import career_engine
from app.services.parser_service import ResumeParserService
from app.ai.providers import ollama


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    user = User(email="test@example.com", hashed_password="test", is_active=True)
    session.add(user)
    session.commit()
    app = FastAPI()
    for router in [resume.router, reports.router, coach.router]:
        app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[get_current_user] = lambda: user
    monkeypatch.setattr(resume, "UPLOAD_DIR", str(tmp_path / "uploads"))
    with TestClient(app) as test_client:
        yield test_client, session, user
    session.close()
    engine.dispose()


def upload(client, text="Python, SQL, Git"):
    document = docx.Document()
    document.add_paragraph(text)
    stream = BytesIO()
    document.save(stream)
    response = client.post("/api/v1/resume/upload", files={"file": ("resume.docx", stream.getvalue())})
    assert response.status_code == 201, response.text
    return response.json()


def analyze(client, resume_id, role="Backend Developer"):
    return client.post("/api/v1/analysis/analyze", json={
        "resume_id": resume_id, "job_role": role, "field": "Technology", "experience_level": "Unspecified",
    })


def test_no_fabricated_resume_data():
    parsed = ResumeParserService.parse_resume_content("Retail assistant with customer service experience")
    assert parsed["technical_skills"] == []
    assert parsed["education"] == []
    assert parsed["experience"] == []
    assert parsed["contact"]["email"] is None


@pytest.mark.parametrize("role", list(career_graph.roles))
def test_every_role_has_extractable_skills_and_honest_extremes(role):
    required = career_graph.roles[role]["required_skills"]
    parsed = ResumeParserService.parse_resume_content(", ".join(required))
    full = career_engine.evaluate_candidate(parsed["technical_skills"], role)
    assert full["match_percent"] == 100
    assert full["missing_skills"] == []
    empty = career_engine.evaluate_candidate([], role)
    assert empty["match_percent"] == 0
    assert empty["matched_skills"] == []


def test_aliases_and_word_boundaries():
    parsed = ResumeParserService.parse_resume_content("sklearn; Amazon Web Services; RESTful APIs; C++; Django")
    assert "Scikit-Learn" in parsed["technical_skills"]
    assert "AWS" in parsed["technical_skills"]
    assert "REST API" in parsed["technical_skills"]
    assert "C++" in parsed["technical_skills"]
    assert "Go" not in parsed["technical_skills"]


def test_upload_analysis_and_chat_use_same_resume(client, monkeypatch):
    api, db, user = client
    uploaded = upload(api)
    response = analyze(api, uploaded["id"])
    assert response.status_code == 201
    report = response.json()
    assert report["analysis_data"]["match_percent"] == 50
    assert set(report["analysis_data"]["matched_skills"]) == {"Python", "SQL", "Git"}
    assert report["gap_analysis"]["learning_steps"]
    upload(api, "Tableau, Statistics, Excel")
    context = api.get("/api/v1/chat/context").json()
    assert context["report_id"] == report["id"]
    captured = []
    def fake_post(url, **kwargs):
        captured.append(kwargs["json"])
        return httpx.Response(200, json={"message": {"content": "Practice FastAPI with a small API."}}, request=httpx.Request("POST", url))
    monkeypatch.setattr(ollama.httpx, "post", fake_post)
    reply = api.post("/api/v1/chat/message", json={"content": "What should I learn first?"})
    assert reply.status_code == 200, reply.text
    prompt = captured[0]["messages"][1]["content"]
    assert "Python, SQL, Git" in prompt
    assert "Tableau, Statistics, Excel" not in prompt
    assert captured[0]["stream"] is False
    assert len(api.get("/api/v1/chat/history").json()["messages"]) == 2
    api.post("/api/v1/chat/message", json={"content": "Explain that project"})
    assert "What should I learn first?" in captured[1]["messages"][1]["content"]
    # A changed role starts a new conversation.
    assert analyze(api, uploaded["id"], "Data Analyst").status_code == 201
    assert api.get("/api/v1/chat/history").json()["messages"] == []
    assert api.delete("/api/v1/chat/clear").status_code == 204


def test_invalid_uploads_and_foreign_resumes(client):
    api, db, user = client
    assert api.post("/api/v1/resume/upload", files={"file": ("bad.pdf", b"not a PDF")}).status_code == 400
    assert api.post("/api/v1/resume/upload", files={"file": ("old.doc", b"content")}).status_code == 400
    assert api.post("/api/v1/resume/upload", files={"file": ("large.pdf", b"x" * (5 * 1024 * 1024 + 1))}).status_code == 400
    other = User(email="other@example.com", hashed_password="test")
    db.add(other)
    db.flush()
    foreign = ResumeSession(user_id=other.id, session_uuid="other", file_name="other.docx", file_type=".docx", file_path="unused")
    db.add(foreign)
    db.commit()
    assert analyze(api, foreign.id).status_code == 404
    uploaded = upload(api)
    assert analyze(api, uploaded["id"], "Unsupported").status_code == 400


def test_chat_requires_analysis_and_handles_ollama_failure(client, monkeypatch):
    api, _, _ = client
    assert api.post("/api/v1/chat/message", json={"content": "Help me"}).status_code == 400
    assert api.post("/api/v1/chat/message", json={"content": "  "}).status_code == 422
    assert api.post("/api/v1/chat/message", json={"content": "x" * 2001}).status_code == 422
    uploaded = upload(api)
    analyze(api, uploaded["id"])
    monkeypatch.setattr(ollama.httpx, "post", Mock(side_effect=httpx.ConnectError("offline")))
    response = api.post("/api/v1/chat/message", json={"content": "Help with my resume"})
    assert response.status_code == 503
    assert "Ollama" in response.json()["detail"]
    assert api.get("/api/v1/chat/history").json()["messages"] == []

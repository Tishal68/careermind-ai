from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
import json

import httpx
import pytest
from fastapi import HTTPException
from pydantic import SecretStr
from sqlalchemy.orm import sessionmaker

from test_career_flow import client, upload
from app.schemas import ResearchRequest
from app.services import job_research as research, research_worker
from app.models.research import ResearchJob
from app.models.report import CareerReport
from app.models.user import User
from app.core.config import settings
from app.ai.providers.ollama import OllamaLLMProvider


TEXT = "Acme seeks a Junior Designer in London. Figma is required. Portfolio preferred. Apply today for this design position."
RESUME = "Designed accessible prototypes using Figma for a student project."


def request(**kwargs):
    return ResearchRequest(resume_id=1, job_role="Designer", location="London", experience_level="Junior", **kwargs)


def source(index=0, kind="market"):
    return {"text": TEXT.replace("Acme", f"Acme{index}"), "url": f"https://jobs.example.com/{index}",
            "retrieved_at": datetime.now(timezone.utc).isoformat(), "kind": kind}


def extracted(index=0, **overrides):
    data = dict(source_id=index, is_job_posting=True, title="Junior Designer", title_quote="Junior Designer",
                company=f"Acme{index}", location="London", role_match=True, location_match=True,
                level_match=True, comparison_reason="Junior design role in London.",
                comparison_quote="Junior Designer in London", closed=False,
                requirements=[dict(name="Figma", kind="skill", importance="required", source_quote="Figma is required",
                                   resume_status="evidenced", resume_quote="using Figma"),
                              dict(name="Portfolio", kind="skill", importance="preferred", source_quote="Portfolio preferred",
                                   resume_status="not_found", resume_quote="")])
    data.update(overrides)
    return research.ExtractedJob.model_validate(data)


@pytest.mark.parametrize("url", ["http://example.com/job", "https://127.0.0.1/job", "https://192.168.1.1/job",
                                     "https://localhost/job", "https://x.internal/job", "https://user:password@example.com/job",
                                     "javascript:alert(1)", "https://example.com:8000/job"])
def test_unsafe_urls_rejected(url):
    with pytest.raises(HTTPException):
        research.public_url(url)


def test_evidence_weighting_and_fabricated_resume_quote():
    job = extracted()
    result = research.evaluate_job(job, source(), RESUME)
    assert result["coverage"] == 67  # required=2, preferred=1
    job.requirements[0].resume_quote = "Invented experience"
    result = research.evaluate_job(job, source(), RESUME)
    assert result["coverage"] == 0
    assert result["requirements"][0]["resume_status"] == "not_found"
    job.requirements[0].source_quote = "Not in the job page"
    assert len(research.evaluate_job(job, source(), RESUME)["requirements"]) == 1


def test_closed_nonjob_and_unverified_title_excluded():
    assert research.evaluate_job(extracted(is_job_posting=False), source(), RESUME) is None
    assert research.evaluate_job(extracted(title_quote="Invented title"), source(), RESUME) is None
    closed = source()
    closed["text"] += " Applications are closed. Closing date 2020-01-01."
    assert research.evaluate_job(extracted(closed=True, closure_quote="Applications are closed"), closed, RESUME) is None
    assert research.evaluate_job(extracted(closing_date="2020-01-01", closure_quote="Closing date 2020-01-01"), closed, RESUME) is None


def test_market_frequencies_filter_mismatches_and_company_stays_separate(monkeypatch):
    sources = [source(i) for i in range(4)]
    monkeypatch.setattr(research, "market_sources", lambda req: (sources, []))
    jobs = [extracted(i) for i in range(3)] + [extracted(3, location_match=False)] + [extracted(4)]
    monkeypatch.setattr(research, "extract", lambda *args: research.Extraction(jobs=jobs))
    analysis, gap = research.research(request(job_description=TEXT), RESUME)
    snapshot = analysis["research"]
    assert snapshot["sample_size"] == 3
    assert snapshot["typical_requirements"][0]["posting_count"] == 3
    assert snapshot["typical_requirements"][0]["frequency_percent"] == 100
    assert len(snapshot["excluded_comparisons"]) == 1
    assert snapshot["company_match"]["coverage"] == 67
    assert analysis["match_percent"] == 67
    assert gap["missing_skills"] == ["Portfolio"]


def test_small_sample_never_claims_typical_market_and_duplicates_not_counted(monkeypatch):
    monkeypatch.setattr(research, "market_sources", lambda req: ([source(), source()], []))
    monkeypatch.setattr(research, "extract", lambda *args: research.Extraction(jobs=[extracted(), extracted(1, company="Acme0")]))
    analysis, _ = research.research(request(), RESUME)
    assert analysis["research"]["sample_size"] == 1
    assert analysis["research"]["typical_requirements"] == []
    assert analysis["match_percent"] is None
    assert analysis["research"]["warnings"]


def test_pasted_description_works_without_search_key(monkeypatch):
    monkeypatch.setattr(settings, "OLLAMA_API_KEY", SecretStr(""))
    monkeypatch.setattr(research, "extract", lambda *args: research.Extraction(jobs=[extracted()]))
    analysis, _ = research.research(request(search_market=False, job_description=TEXT), RESUME)
    assert analysis["research"]["company_match"]
    assert not analysis["research"]["best_fit_openings"]
    with pytest.raises(HTTPException) as exc:
        research.research(request(), RESUME)
    assert "OLLAMA_API_KEY" in exc.value.detail


def test_search_cache_deduplication_and_no_resume_in_queries(monkeypatch):
    research._cache.clear()
    calls = []
    def call(endpoint, payload):
        calls.append((endpoint, payload))
        if endpoint == "web_search":
            return {"results": [{"url": "https://jobs.example.com/1?utm_source=x"}, {"url": "https://jobs.example.com/1"}]}
        return {"content": TEXT}
    monkeypatch.setattr(research, "web_call", call)
    first, _ = research.market_sources(request())
    second, warnings = research.market_sources(request())
    assert len(first) == len(second) == 1
    assert len(calls) == 3
    assert "Designer" in calls[0][1]["query"]
    assert RESUME not in str(calls)
    assert "cached" in warnings[-1]
    first.append({"kind": "company", "text": "Private pasted company description"})
    second[0]["text"] = "Changed copy"
    cached, _ = research.market_sources(request())
    assert len(cached) == 1
    assert cached[0]["text"] == TEXT
    research.market_sources(request(refresh=True))
    assert len(calls) == 6
    research._cache.clear()


def test_cloud_json_does_not_send_unsupported_format(monkeypatch):
    def post(url, **kwargs):
        assert "format" not in kwargs["json"]
        assert "schema" in kwargs["json"]["messages"][1]["content"]
        return httpx.Response(200, json={"message": {"content": '```json\n{"jobs": []}\n```'}}, request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "post", post)
    assert OllamaLLMProvider(base_url="https://ollama.com").generate_json("extract", {"type": "object"}) == {"jobs": []}


def test_extraction_validation_retry_is_bounded(monkeypatch):
    generate = Mock(return_value={"invented": "invalid"})
    monkeypatch.setattr(OllamaLLMProvider, "generate_json", generate)
    with pytest.raises(HTTPException) as error:
        research.extract([source()], RESUME, request())
    assert error.value.status_code == 502
    assert generate.call_count == 2


def test_background_api_persists_report_and_coach_sources(client, monkeypatch):
    api, db, user = client
    monkeypatch.setattr(research_worker, "SessionLocal", sessionmaker(bind=db.get_bind()))
    monkeypatch.setattr(research, "extract", lambda *args: research.Extraction(jobs=[extracted()]))
    uploaded = upload(api, RESUME)
    response = api.post("/api/v1/analysis/research", json={
        **request(search_market=False, job_description=TEXT).model_dump(), "resume_id": uploaded["id"]})
    assert response.status_code == 202, response.text
    state = api.get(f'/api/v1/analysis/research/{response.json()["id"]}').json()
    assert state["status"] == "completed", state
    assert state["report"]["job_role"] == "Designer"  # Not one of the static roles
    assert state["report"]["analysis_data"]["research"]["company_match"]["coverage"] == 67
    context = api.get("/api/v1/chat/context").json()
    assert context["research"]["company_match"]["requirements"][0]["source_quote"] == "Figma is required"
    persisted = db.get(ResearchJob, response.json()["id"])
    assert "job_description" not in persisted.request_data


def test_background_failures_and_foreign_status_are_private(client, monkeypatch):
    api, db, user = client
    monkeypatch.setattr(research_worker, "SessionLocal", sessionmaker(bind=db.get_bind()))
    monkeypatch.setattr(research_worker, "research", Mock(side_effect=HTTPException(503, "Ollama usage limit reached.")))
    uploaded = upload(api, RESUME)
    response = api.post("/api/v1/analysis/research", json={
        **request(search_market=False, job_description=TEXT).model_dump(), "resume_id": uploaded["id"]})
    state = api.get(f'/api/v1/analysis/research/{response.json()["id"]}').json()
    assert state["status"] == "failed"
    assert "usage limit" in state["error"]
    assert db.query(CareerReport).count() == 0
    other = User(email="private@example.com", hashed_password="test")
    db.add(other)
    db.flush()
    foreign = ResearchJob(user_id=other.id, request_data={})
    db.add(foreign)
    db.commit()
    assert api.get(f"/api/v1/analysis/research/{foreign.id}").status_code == 404
    expired = ResearchJob(user_id=user.id, request_data={}, created_at=datetime.now(timezone.utc) - timedelta(minutes=11))
    db.add(expired)
    db.commit()
    assert api.get(f"/api/v1/analysis/research/{expired.id}").json()["status"] == "failed"


def test_active_task_prevents_duplicate_and_input_errors_are_actionable(client):
    api, db, user = client
    uploaded = upload(api, RESUME)
    payload = {**request(search_market=False, job_description=TEXT).model_dump(), "resume_id": uploaded["id"]}
    active = ResearchJob(user_id=user.id, status="running", request_data={})
    db.add(active)
    db.commit()
    assert api.post("/api/v1/analysis/research", json=payload).status_code == 409
    assert api.post("/api/v1/analysis/research", json={**payload, "job_role": " "}).status_code == 422
    assert api.post("/api/v1/analysis/research", json={**payload, "job_description": ""}).status_code == 422
    assert api.post("/api/v1/analysis/research", json={**payload, "job_url": "http://localhost/private"}).status_code == 422
    assert api.post("/api/v1/analysis/research", json={**payload, "resume_id": 987654}).status_code == 404


def test_eligibility_gap_is_not_presented_as_a_course(monkeypatch):
    text = TEXT + " Must hold a professional license."
    job = extracted()
    job.requirements.append(research.Requirement(name="Professional license", kind="eligibility", importance="required",
                                                source_quote="Must hold a professional license", resume_status="not_found"))
    monkeypatch.setattr(research, "extract", lambda *args: research.Extraction(jobs=[job]))
    _, gap = research.research(request(search_market=False, job_description=text), RESUME)
    assert gap["learning_steps"][0].startswith("Verify Professional license")


def test_timeout_error_explains_model_latency(monkeypatch):
    monkeypatch.setattr(httpx, "post", Mock(side_effect=httpx.ReadTimeout("timeout")))
    with pytest.raises(HTTPException) as exc:
        OllamaLLMProvider().generate_text("Career advice")
    assert "took too long" in exc.value.detail

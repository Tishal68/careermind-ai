from concurrent.futures import ThreadPoolExecutor
from app.models import CareerReport, User
from test_reliability import queue_db, client_for


def seed(factory, uid, rid, gaps, research=None):
    with factory() as db:
        report = CareerReport(user_id=uid, resume_session_id=rid, field="Career research", job_role="Product Designer", experience_level="Junior", gap_analysis={"missing_skills": gaps}, analysis_data={"research": research} if research else {})
        db.add(report); db.commit(); return report.id


def test_plan_persists_and_repeated_creation_preserves_progress(queue_db):
    factory, uid, rid = queue_db
    report_id = seed(factory, uid, rid, ["User research", "Prototyping"])
    url = f"/api/v1/analysis/reports/{report_id}/action-plan"
    with client_for(factory, uid) as c:
        assert c.get(url).json()["created"] is False
        plan = c.post(url).json()
        assert plan["job_role"] == "Product Designer"
        assert len(plan["projects"]) == 2
        assert "RAG" not in str(plan)
        task = plan["milestones"][0]["tasks"][0]
        saved = c.patch(url+"/tasks/"+task["id"], json={"revision": 1, "is_completed": True})
        assert saved.status_code == 200
        assert saved.json()["revision"] == 2
    with client_for(factory, uid) as c:
        assert c.get(url).json()["milestones"][0]["tasks"][0]["is_completed"] is True
        assert c.post(url).json()["revision"] == 2
        assert c.post(f"/api/v1/roadmap/generate/{report_id}").json()["milestones"][0]["tasks"][0]["is_completed"] is True


def test_plan_ownership_and_project_context(queue_db):
    factory, uid, rid = queue_db
    report_id = seed(factory, uid, rid, ["User research"])
    with factory() as db:
        other = User(email="other-plan@example.com", hashed_password="test");db.add(other);db.commit();other_id=other.id
    url=f"/api/v1/analysis/reports/{report_id}/action-plan"
    with client_for(factory, other_id) as c:
        assert c.get(url).status_code == 404
        assert c.post(url).status_code == 404
        assert c.patch(url+"/tasks/p1-t1", json={"revision":1,"is_completed":True}).status_code == 404
        assert c.get(f"/api/v1/projects/recommendations?report_id={report_id}").status_code == 404
    with client_for(factory, uid) as c:
        assert c.get("/api/v1/projects/recommendations").status_code == 422
        assert c.get(f"/api/v1/projects/recommendations?report_id={report_id}").json()[0]["required_skills"] == ["User research"]


def test_no_gap_no_invented_plan(queue_db):
    factory, uid, rid=queue_db
    for research in [None, {"company_match": None, "typical_requirements": [], "sample_status": "insufficient_evidence"}]:
        report_id=seed(factory,uid,rid,[] if research is None else ["Do not infer typical gaps"], research)
        with client_for(factory,uid) as c:
            result=c.post(f"/api/v1/analysis/reports/{report_id}/action-plan").json()
            assert result["created"] is True
            assert result["milestones"] == [] and result["projects"] == []


def test_eligibility_is_not_a_practice_project(queue_db):
    factory,uid,rid=queue_db
    research={"company_match":{"requirements":[
        {"name":"Work authorization", "kind":"eligibility", "resume_status":"not_found", "importance":"required"},
        {"name":"Prototyping", "kind":"skill", "resume_status":"partial", "importance":"preferred"},
        {"name":"User research", "kind":"skill", "resume_status":"evidenced", "importance":"required"}]}}
    report_id=seed(factory,uid,rid,[],research)
    with client_for(factory,uid) as c:
        plan=c.post(f"/api/v1/analysis/reports/{report_id}/action-plan").json()
        assert plan["milestones"][0]["title"] == "Verify Work authorization"
        assert len(plan["projects"]) == 1
        assert plan["projects"][0]["required_skills"] == ["Prototyping"]


def test_concurrent_edits_detect_conflict(queue_db):
    factory,uid,rid=queue_db
    report_id=seed(factory,uid,rid,["SQL"])
    url=f"/api/v1/analysis/reports/{report_id}/action-plan"
    with client_for(factory,uid) as c:
        c.post(url)
        assert c.patch(url+"/tasks/missing",json={"revision":1,"is_completed":True}).status_code == 404
    def edit(task):
        with client_for(factory,uid) as c:
            return c.patch(url+"/tasks/"+task,json={"revision":1,"is_completed":True}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(edit,["p1-t1","p1-t2"])) == [200,409]
    with client_for(factory,uid) as c:
        plan=c.get(url).json()
        assert plan["revision"] == 2
        assert sum(t["is_completed"] for t in plan["milestones"][0]["tasks"]) == 1

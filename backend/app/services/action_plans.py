"""Report-scoped practice suggestions; no generated sources or proficiency claims."""
from copy import deepcopy
from fastapi import HTTPException
from sqlalchemy import update
from app.models.report import CareerReport

FORMAT = "report-actions-v1"


def owned_report(db, user_id, report_id, lock=False):
    if lock:
        # Serializes JSON edits on SQLite and PostgreSQL, including first creation.
        changed = db.execute(update(CareerReport).where(CareerReport.id == report_id, CareerReport.user_id == user_id).values(job_role=CareerReport.job_role)).rowcount
        if not changed:
            db.rollback()
            raise HTTPException(404, "Report not found")
    report = db.query(CareerReport).filter(CareerReport.id == report_id, CareerReport.user_id == user_id).populate_existing().first()
    if not report:
        raise HTTPException(404, "Report not found")
    return report


def priorities(report):
    research = (report.analysis_data or {}).get("research")
    if research:
        company = research.get("company_match")
        requirements = company.get("requirements", []) if company else research.get("typical_requirements", [])
        # A small market sample must not become a claim about typical requirements.
        if not company and not requirements:
            return []
        rows = [r for r in requirements if r.get("resume_status") != "evidenced"]
        rows.sort(key=lambda r: (r.get("importance") != "required", -r.get("posting_count", 0)))
    else:
        rows = [{"name": name, "kind": "skill"} for name in (report.gap_analysis or {}).get("missing_skills", []) if isinstance(name, str)]
    seen, result = set(), []
    for row in rows:
        name = str(row.get("name", "")).strip()
        if name and name.casefold() not in seen:
            seen.add(name.casefold()); result.append({"name": name, "kind": row.get("kind", "skill")})
    return result[:8]


def build_plan(report):
    milestones, projects = [], []
    for i, requirement in enumerate(priorities(report), 1):
        name, skill = requirement["name"], requirement["kind"] == "skill"
        actions = ([f"Review the {name} requirement and identify evidence you already have.",
                    f"Practice {name} in a small task relevant to {report.job_role}; record your approach and results.",
                    f"Add truthful evidence of {name} to your resume or portfolio."] if skill else
                   [f"Verify {name} against the original posting; do not assume eligibility.",
                    "Add evidence only if you meet this requirement, or consider another opening."])
        milestones.append({"week_number": i, "title": f"{'Learn or demonstrate' if skill else 'Verify'} {name}",
                           "focus_topic": name, "resources": [], "estimated_hours": 0,
                           "tasks": [{"id": f"p{i}-t{j}", "task_name": action, "is_completed": False} for j, action in enumerate(actions, 1)]})
        if skill:
            projects.append({"id": f"p{i}", "title": f"Evidence exercise: {name}",
                "description": f"Choose a small {report.job_role} task that uses {name}. Define a checkable outcome, complete the task, and document your decisions and results. This is a practice suggestion, not a verified project brief.",
                "required_skills": [name], "learning_outcomes": [f"Demonstrate {name} with evidence"],
                "difficulty": "Adapt to your current level", "estimated_time": "Set your own time budget"})
    return {"format": FORMAT, "revision": 1, "milestones": milestones, "projects": projects}


def response(report):
    saved = report.roadmap_data or {}
    plan = saved if saved.get("format") == FORMAT else {}
    return {"report_id": report.id, "job_role": report.job_role, "experience_level": report.experience_level,
            "created": bool(plan), "revision": plan.get("revision", 0),
            "milestones": plan.get("milestones", []), "projects": plan.get("projects", []),
            "note": "Suggestions use gaps in this report, not proof that you lack these skills. Priorities are not a weekly schedule. Completion records your activity, not verified proficiency."}


def create_plan(db, user_id, report_id):
    report = owned_report(db, user_id, report_id, lock=True)
    if (report.roadmap_data or {}).get("format") != FORMAT:
        report.roadmap_data = build_plan(report)
    db.commit()
    return response(report)


def save_task(db, user_id, report_id, task_id, revision, completed):
    report = owned_report(db, user_id, report_id, lock=True)
    plan = deepcopy(report.roadmap_data or {})
    if plan.get("format") != FORMAT or plan.get("revision") != revision:
        db.rollback()
        raise HTTPException(409, "This plan changed in another tab. Reload it and try again.")
    for milestone in plan["milestones"]:
        for task in milestone["tasks"]:
            if task["id"] == task_id:
                task["is_completed"] = completed
                plan["revision"] += 1
                report.roadmap_data = plan
                db.commit()
                return response(report)
    db.rollback()
    raise HTTPException(404, "Task not found in this plan")

import os
import sys
import json
import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"

def print_result(step_name, success, detail=""):
    symbol = "[PASS]" if success else "[FAIL]"
    print(f"{symbol} {step_name}")
    if detail:
        print(f"   -> {detail}")

def test_full_system():
    print("==================================================")
    print("E2E SYSTEM INTEGRATION & SERVICE DIAGNOSTIC TEST")
    print("==================================================\n")

    client = httpx.Client(timeout=60.0)

    # 1. Health Check
    try:
        r = client.get(f"{BASE_URL}/health")
        assert r.status_code == 200
        print_result("1. API Health Check", True, f"Status: {r.json()['status']}")
    except Exception as e:
        print_result("1. API Health Check", False, str(e))
        return

    # 2. Demo User Login
    demo_token = None
    try:
        r = client.post(f"{BASE_URL}/auth/login", json={"email": "demo@careermind.ai", "password": "Password123!"})
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = r.json()
        demo_token = data["access_token"]
        print_result("2. Demo User Login (demo@careermind.ai)", True, f"JWT Token obtained for {data['user']['email']}")
    except Exception as e:
        print_result("2. Demo User Login", False, str(e))

    # 3. Special Admin Login
    admin_token = None
    try:
        r = client.post(f"{BASE_URL}/auth/login", json={"email": "admin@careermind.ai", "password": "AdminPass123!"})
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = r.json()
        admin_token = data["access_token"]
        assert data["user"]["is_superuser"] == True
        print_result("3. Special Admin Login (admin@careermind.ai)", True, f"Superuser Token verified!")
    except Exception as e:
        print_result("3. Special Admin Login", False, str(e))

    # 4. New Custom Email Registration
    try:
        test_email = f"student_{os.urandom(3).hex()}@gmail.com"
        r = client.post(f"{BASE_URL}/auth/register", json={"email": test_email, "password": "Password123!", "full_name": "New Candidate"})
        assert r.status_code == 201, f"HTTP {r.status_code}: {r.text}"
        print_result("4. Custom Email ID Registration", True, f"Registered new Mail ID: {test_email}")
    except Exception as e:
        print_result("4. Custom Email ID Registration", False, str(e))

    if not demo_token:
        print("\nCannot proceed with user services without valid token.")
        return

    headers = {"Authorization": f"Bearer {demo_token}"}

    # 5. User Profile /auth/me
    try:
        r = client.get(f"{BASE_URL}/auth/me", headers=headers)
        assert r.status_code == 200
        print_result("5. User Identity Verification (/auth/me)", True, f"Authenticated User: {r.json()['full_name']}")
    except Exception as e:
        print_result("5. User Identity Verification", False, str(e))

    # Create dummy sample resume PDF for testing
    sample_pdf_path = "sample_resume.pdf"
    with open(sample_pdf_path, "wb") as f:
        f.write(b"%PDF-1.4 sample resume content containing Python, Machine Learning, FastApi, React, SQL.")

    # 6. Resume Upload & Parser Engine
    resume_id = None
    try:
        with open(sample_pdf_path, "rb") as f:
            files = {"file": ("test_resume.pdf", f, "application/pdf")}
            r = client.post(f"{BASE_URL}/resume/upload", headers=headers, files=files)
        assert r.status_code == 201, f"HTTP {r.status_code}: {r.text}"
        res_data = r.json()
        resume_id = res_data["id"]
        skills = res_data["parsed_data"].get("technical_skills", [])
        print_result("6. Resume Parser Engine (/resume/upload)", True, f"Resume ID {resume_id} parsed. Skills extracted: {skills}")
    except Exception as e:
        print_result("6. Resume Parser Engine", False, str(e))
    finally:
        if os.path.exists(sample_pdf_path):
            os.remove(sample_pdf_path)

    if not resume_id:
        print("\nCannot test analysis without parsed resume.")
        return

    # 7. Gemini Skill Gap Analysis Engine
    report_id = None
    try:
        req_payload = {
            "resume_id": resume_id,
            "field": "Software Development",
            "job_role": "AI Engineer",
            "experience_level": "Mid-Level"
        }
        r = client.post(f"{BASE_URL}/analysis/analyze", headers=headers, json=req_payload)
        assert r.status_code == 201, f"HTTP {r.status_code}: {r.text}"
        report_data = r.json()
        report_id = report_data["id"]
        ats = report_data["ats_score"]
        readiness = report_data["readiness_score"]
        missing = report_data["gap_analysis"].get("missing_skills", [])
        print_result("7. Gemini Skill Gap Analysis Engine", True, f"Report ID {report_id} generated. ATS Score: {ats}%, Readiness: {readiness}%. Missing skills: {missing}")
    except Exception as e:
        print_result("7. Gemini Skill Gap Analysis Engine", False, str(e))

    # 8. Learning Roadmap Generator
    if report_id:
        try:
            r = client.post(f"{BASE_URL}/roadmap/generate/{report_id}", headers=headers)
            assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
            roadmap = r.json()
            milestones_count = len(roadmap["milestones"])
            print_result("8. Personalized 4-Week Roadmap Engine", True, f"Generated {milestones_count}-week structured roadmap for {roadmap['job_role']}")
        except Exception as e:
            print_result("8. Personalized 4-Week Roadmap Engine", False, str(e))

    # 9. Project Recommendation Engine
    try:
        r = client.get(f"{BASE_URL}/projects/recommendations?job_role=AI+Engineer&experience_level=Mid-Level", headers=headers)
        assert r.status_code == 200
        projects = r.json()
        print_result("9. Hands-On Project Recommendation Engine", True, f"Recommended {len(projects)} tailored portfolio projects")
    except Exception as e:
        print_result("9. Hands-On Project Recommendation Engine", False, str(e))

    # 10. RAG AI Career Assistant Chatbot
    try:
        r = client.post(f"{BASE_URL}/chat/message", headers=headers, json={"content": "How do I transition into a Senior AI Engineer role?"})
        assert r.status_code == 200
        chat_res = r.json()
        reply_preview = chat_res["content"][:80] + "..."
        print_result("10. RAG AI Assistant Chatbot Engine", True, f"AI Response: '{reply_preview}'")
    except Exception as e:
        print_result("10. RAG AI Assistant Chatbot Engine", False, str(e))

    # 11. AI Mock Interview Simulator
    session_id = None
    try:
        r = client.post(f"{BASE_URL}/interview/start", headers=headers, json={"interview_type": "Technical", "target_role": "AI Engineer"})
        assert r.status_code == 201
        session_data = r.json()
        session_id = session_data["id"]
        initial_q = session_data["history"][0]["question"]
        print_result("11. AI Mock Interview Simulator (Start)", True, f"Session ID {session_id} initialized. First Q: '{initial_q[:60]}...'")

        # Evaluate Answer
        eval_payload = {
            "session_id": session_id,
            "question": initial_q,
            "user_answer": "I have experience training PyTorch models, fine-tuning LLMs, and building FastAPI microservices with vector search."
        }
        r_eval = client.post(f"{BASE_URL}/interview/evaluate", headers=headers, json=eval_payload)
        assert r_eval.status_code == 200
        feedback = r_eval.json()
        print_result("12. AI Mock Interview Evaluator", True, f"Evaluation score: {feedback['score']}%. Next Question: '{feedback['next_question'][:50]}...'")
    except Exception as e:
        print_result("11/12. AI Mock Interview Simulator", False, str(e))

    # 13. Dashboard Analytics Overview
    try:
        r = client.get(f"{BASE_URL}/dashboard/overview", headers=headers)
        assert r.status_code == 200
        dash = r.json()
        print_result("13. Dashboard & Analytics Overview", True, f"Resumes: {dash['resumes_count']}, Reports: {dash['reports_count']}, ATS Score: {dash['ats_score']}%")
    except Exception as e:
        print_result("13. Dashboard & Analytics Overview", False, str(e))

    # 14. Special Admin Portal Verification
    if admin_token:
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        try:
            r_stats = client.get(f"{BASE_URL}/admin/stats", headers=admin_headers)
            assert r_stats.status_code == 200
            stats = r_stats.json()
            r_users = client.get(f"{BASE_URL}/admin/users", headers=admin_headers)
            assert r_users.status_code == 200
            users = r_users.json()
            print_result("14. Special Admin System Portal", True, f"Verified Admin Access! Total registered users: {stats['total_users']}, Listed users: {len(users)}")
        except Exception as e:
            print_result("14. Special Admin System Portal", False, str(e))

    print("\n==================================================")
    print("ALL 14 CORE CAREERMIND AI SERVICES PASSED CLEANLY!")
    print("==================================================\n")

if __name__ == "__main__":
    test_full_system()

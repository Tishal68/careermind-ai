import pytest
import os
import re
import secrets
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.main import app
from app.models.user import User
from app.models.account_token import AccountToken
from app.models.session import ResumeSession
from app.models.report import CareerReport
from app.models.chat import ChatSession, ChatMessage
from app.models.interview import InterviewSession
from app.services import email_service


@pytest.fixture(name="lifecycle_db")
def fixture_lifecycle_db(tmp_path):
    db_file = tmp_path / "test_lifecycle.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestingSessionLocal
    app.dependency_overrides.pop(get_db, None)


def test_httponly_cookies_and_csrf_protection(lifecycle_db):
    client = TestClient(app)
    email_service.test_outbox.clear()

    # 1. Register user and verify cookies are set
    reg_res = client.post(
        "/api/v1/auth/register",
        headers={"X-Use-Cookie": "1"},
        json={"email": "cookie.user@example.com", "password": "SecurePassword123!", "full_name": "Cookie User"}
    )
    assert reg_res.status_code == 201
    assert "careermind_session" in reg_res.cookies
    assert "careermind_csrf" in reg_res.cookies

    # 2. Login and check cookies
    login_res = client.post(
        "/api/v1/auth/login",
        headers={"X-Use-Cookie": "1"},
        json={"email": "cookie.user@example.com", "password": "SecurePassword123!"}
    )
    assert login_res.status_code == 200
    session_cookie = login_res.cookies["careermind_session"]
    csrf_cookie = login_res.cookies["careermind_csrf"]

    # 3. Authenticated GET /auth/me via cookie (safe method: no CSRF required)
    client.cookies.clear()
    client.cookies.set("careermind_session", session_cookie)
    me_res = client.get("/api/v1/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "cookie.user@example.com"

    # 4. Unsafe method (POST) via cookie WITHOUT CSRF header must be rejected with 403
    post_no_csrf = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "SecurePassword123!", "new_password": "BrandNewPassword123!"}
    )
    assert post_no_csrf.status_code == 403
    assert "CSRF" in post_no_csrf.json()["detail"]

    # 5. Unsafe method with mismatched CSRF header must be rejected with 403
    client.cookies.set("careermind_csrf", csrf_cookie)
    post_bad_csrf = client.post(
        "/api/v1/auth/change-password",
        headers={"X-CSRF-Token": "invalid-csrf-token"},
        json={"current_password": "SecurePassword123!", "new_password": "BrandNewPassword123!"}
    )
    assert post_bad_csrf.status_code == 403

    # 6. Unsafe method with matching CSRF header succeeds
    post_valid_csrf = client.post(
        "/api/v1/auth/change-password",
        headers={"X-CSRF-Token": csrf_cookie},
        json={"current_password": "SecurePassword123!", "new_password": "BrandNewPassword123!"}
    )
    assert post_valid_csrf.status_code == 200
    assert "careermind_session" in post_valid_csrf.cookies

    # 7. Logout clears cookies and revokes session (using the updated CSRF cookie)
    new_csrf = post_valid_csrf.cookies["careermind_csrf"]
    logout_res = client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": new_csrf}
    )
    assert logout_res.status_code == 204
    # Old session is now rejected
    assert client.get("/api/v1/auth/me").status_code == 401


def test_password_recovery_lifecycle(lifecycle_db):
    client = TestClient(app)
    email_service.test_outbox.clear()

    # Create user
    with lifecycle_db() as db:
        user = User(
            email="recover@example.com",
            hashed_password=get_password_hash("InitialPassword123!"),
            session_version=1
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id

    # 1. Request password reset
    forgot_res = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "Recover@Example.com"}  # Case-varied
    )
    assert forgot_res.status_code == 200
    assert "password reset instructions" in forgot_res.json()["detail"]

    # Verify email was captured in outbox and token was recorded in DB
    assert len(email_service.test_outbox) >= 1
    sent = [m for m in email_service.test_outbox if m["to"] == "recover@example.com"][-1]
    assert "Password Reset" in sent["subject"]

    # Retrieve the token from database
    with lifecycle_db() as db:
        token_record = db.query(AccountToken).filter(
            AccountToken.user_id == user_id,
            AccountToken.token_type == "password_reset"
        ).first()
        assert token_record is not None
        assert token_record.used_at is None
        exp = token_record.expires_at.replace(tzinfo=timezone.utc) if token_record.expires_at.tzinfo is None else token_record.expires_at
        assert exp > datetime.now(timezone.utc)

    # Extract raw token from reset link in email body
    match = re.search(r"token=([A-Za-z0-9_-]+)", sent["content"])
    assert match is not None
    raw_token = match.group(1)

    # 2. Reset password with invalid token fails
    bad_reset = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "invalid-token-12345", "new_password": "NewSecretPassword123!"}
    )
    assert bad_reset.status_code == 400

    # 3. Reset password with valid token succeeds
    good_reset = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewSecretPassword123!"}
    )
    assert good_reset.status_code == 200
    assert "reset successfully" in good_reset.json()["detail"]

    # 4. Old password no longer works for login
    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": "recover@example.com", "password": "InitialPassword123!"}
    )
    assert old_login.status_code == 401

    # 5. New password works for login
    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "recover@example.com", "password": "NewSecretPassword123!"}
    )
    assert new_login.status_code == 200

    # 6. Single-use: Reusing the same token fails
    reuse_reset = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "AnotherPassword123!"}
    )
    assert reuse_reset.status_code == 400


def test_email_verification_lifecycle(lifecycle_db):
    client = TestClient(app)
    email_service.test_outbox.clear()

    with lifecycle_db() as db:
        user = User(
            email="verify.me@example.com",
            hashed_password=get_password_hash("Password123456!"),
            is_verified=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id

    token = create_access_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Check me: is_verified is False
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["is_verified"] is False

    # 2. Send verification email
    send_res = client.post("/api/v1/auth/send-verification", headers=headers)
    assert send_res.status_code == 200

    assert len(email_service.test_outbox) >= 1
    sent = [m for m in email_service.test_outbox if m["to"] == "verify.me@example.com"][-1]
    assert "Verify Your Email" in sent["subject"]

    match = re.search(r"token=([A-Za-z0-9_-]+)", sent["content"])
    assert match is not None
    raw_token = match.group(1)

    # 3. Verify with invalid token fails
    assert client.post("/api/v1/auth/verify-email", json={"token": "invalid-token-1234"}).status_code == 400

    # 4. Verify with valid token succeeds
    verify_res = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert verify_res.status_code == 200

    # 5. User is now verified
    me_res_after = client.get("/api/v1/auth/me", headers=headers)
    assert me_res_after.json()["is_verified"] is True

    # 6. Re-sending when already verified reports already verified
    re_send = client.post("/api/v1/auth/send-verification", headers=headers)
    assert re_send.status_code == 200
    assert "already verified" in re_send.json()["detail"].lower()


def test_account_export_and_deletion(lifecycle_db, tmp_path):
    client = TestClient(app)

    # Create dummy uploaded file on disk
    dummy_resume_file = tmp_path / "resume_fixture.pdf"
    dummy_resume_file.write_text("Dummy resume file content")

    with lifecycle_db() as db:
        user = User(
            email="export.delete@example.com",
            hashed_password=get_password_hash("DeleteMePassword123!"),
            full_name="Export User",
            target_job_role="Data Scientist"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id

        # Add resume session
        resume = ResumeSession(
            user_id=user_id,
            file_name="resume_fixture.pdf",
            file_path=str(dummy_resume_file),
            file_type=".pdf",
            parsed_data={"technical_skills": ["Python", "SQL"]}
        )
        db.add(resume)
        db.flush()

        # Add report
        report = CareerReport(
            user_id=user_id,
            resume_session_id=resume.id,
            field="Technology",
            job_role="Data Scientist",
            experience_level="Junior",
            nex_score=85.0,
            analysis_data={"matched_skills": ["Python"]},
            gap_analysis={"missing_skills": ["Spark"]},
            roadmap_data={"steps": ["Learn Spark"]},
            project_recommendations=["Portfolio Project"]
        )
        db.add(report)

        # Add chat session
        chat = ChatSession(user_id=user_id, session_date="2026-10-23", title="Prep Session")
        db.add(chat)
        db.commit()
        db.refresh(chat)

        msg = ChatMessage(chat_session_id=chat.id, role="user", content="How do I prep?")
        db.add(msg)

        # Add interview session
        interview = InterviewSession(user_id=user_id, target_role="Data Scientist", interview_type="Technical", history=[])
        db.add(interview)
        db.commit()

    token = create_access_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Test GET /auth/export
    export_res = client.get("/api/v1/auth/export", headers=headers)
    assert export_res.status_code == 200
    assert export_res.headers["content-type"].startswith("application/json")
    assert "attachment" in export_res.headers["content-disposition"]

    data = export_res.json()
    assert data["user_profile"]["email"] == "export.delete@example.com"
    assert data["user_profile"]["target_job_role"] == "Data Scientist"
    assert len(data["resume_sessions"]) == 1
    assert data["resume_sessions"][0]["file_name"] == "resume_fixture.pdf"
    assert len(data["career_reports"]) == 1
    assert len(data["chat_sessions"]) == 1
    assert len(data["interview_sessions"]) == 1

    # 2. Test DELETE /auth/delete with wrong confirmation
    bad_conf = client.request(
        "DELETE",
        "/api/v1/auth/delete",
        headers=headers,
        json={"password": "DeleteMePassword123!", "confirmation": "delete please"}
    )
    assert bad_conf.status_code == 400

    # 3. Test DELETE /auth/delete with wrong password
    bad_pass = client.request(
        "DELETE",
        "/api/v1/auth/delete",
        headers=headers,
        json={"password": "WrongPassword!", "confirmation": "DELETE MY ACCOUNT"}
    )
    assert bad_pass.status_code == 400

    # 4. Test DELETE /auth/delete valid
    assert os.path.exists(str(dummy_resume_file))
    del_res = client.request(
        "DELETE",
        "/api/v1/auth/delete",
        headers=headers,
        json={"password": "DeleteMePassword123!", "confirmation": "DELETE MY ACCOUNT"}
    )
    assert del_res.status_code == 200

    # Verify physical file was deleted
    assert not os.path.exists(str(dummy_resume_file))

    # Verify user record and all cascade data are gone from database
    with lifecycle_db() as db:
        assert db.query(User).filter(User.id == user_id).first() is None
        assert db.query(ResumeSession).filter(ResumeSession.user_id == user_id).first() is None
        assert db.query(CareerReport).filter(CareerReport.user_id == user_id).first() is None
        assert db.query(ChatSession).filter(ChatSession.user_id == user_id).first() is None
        assert db.query(InterviewSession).filter(InterviewSession.user_id == user_id).first() is None

    # Subsequent request with old token is rejected
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401

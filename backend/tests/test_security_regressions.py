from datetime import timedelta
import bcrypt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.core.config import Settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.api.v1 import auth, admin, resume, settings
from app.models.user import User

@pytest.fixture
def secured():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    app = FastAPI()
    for router in [auth.router, admin.router, resume.router, settings.router]:
        app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        yield client, db
    db.close()
    engine.dispose()

def account(client, email="person@example.com"):
    response = client.post("/api/v1/auth/register", json={"email": email, "password": "private-password", "full_name": "Person"})
    assert response.status_code == 201
    data = response.json()
    return data["user"]["id"], {"Authorization": "Bearer " + data["access_token"]}

@pytest.mark.parametrize("token", [None, "invalid", create_access_token(1, timedelta(seconds=-5)), create_access_token("not-a-number")])
def test_invalid_auth_never_falls_back(secured, token):
    client, db = secured
    account(client)
    headers = {"Authorization": "Bearer " + token} if token else {}
    for path in ["/auth/me", "/resume/my-resumes", "/admin/users"]:
        assert client.get("/api/v1" + path, headers=headers).status_code == 401
    assert db.query(User).count() == 1

def test_admin_authorization_and_toggle(secured):
    client, db = secured
    uid, headers = account(client)
    other, _ = account(client, "other@example.com")
    assert client.get("/api/v1/admin/users", headers=headers).status_code == 403
    assert client.delete(f"/api/v1/admin/users/{other}", headers=headers).status_code == 403
    assert client.post(f"/api/v1/admin/users/{other}/toggle-admin", headers=headers).status_code == 403
    db.get(User, uid).is_superuser = True
    db.commit()
    assert client.get("/api/v1/admin/users", headers=headers).status_code == 200
    assert client.post(f"/api/v1/admin/users/{uid}/toggle-admin", headers=headers).status_code == 400
    assert client.post(f"/api/v1/admin/users/{other}/toggle-admin", headers=headers).json()["is_superuser"] is True

def test_disabled_account_and_invalid_settings(secured):
    client, db = secured
    uid, headers = account(client)
    assert client.put("/api/v1/user/settings", headers=headers, json={"full_name": {"bad": "type"}}).status_code == 422
    assert client.put("/api/v1/user/settings", headers=headers, json={"target_job_role": "Designer"}).status_code == 200
    assert db.get(User, uid).full_name == "Person"
    db.get(User, uid).is_active = False
    db.commit()
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": "person@example.com", "password": "private-password"}).status_code == 401

def test_password_suffix_is_significant_and_legacy_hash_works():
    password = "x" * 72 + "correct"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("x" * 72 + "wrong", hashed)
    legacy = bcrypt.hashpw(b"old-password", bcrypt.gensalt()).decode()
    assert verify_password("old-password", legacy)
    assert not verify_password("wrong", legacy)
    assert not verify_password("anything", "standalone-mode")

@pytest.mark.parametrize("value", ["short", "replace-with-a-long-random-value", "nexpath-super-secret-jwt-key-2026-production-ready"])
def test_public_signing_secrets_rejected(value):
    with pytest.raises(ValueError):
        Settings(SECRET_KEY=value, _env_file=None)

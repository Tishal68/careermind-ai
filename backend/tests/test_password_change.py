import jwt
import pytest

from app.core.config import settings
from test_reliability import queue_db


OLD = "Original-password-123!"
NEW = "Replacement-password-456!"


def account(client):
    response = client.post('/api/v1/auth/register', json={
        'email': 'password-test@example.com', 'full_name': 'Password Test', 'password': OLD})
    assert response.status_code == 201
    return response.json()['access_token']


def headers(token):
    return {'Authorization': f'Bearer {token}'}


def test_change_invalidates_all_old_sessions_and_legacy_tokens(application_client):
    client = application_client
    first = account(client)
    # Model a pre-session-version account, rather than assuming new accounts
    # have the legacy generation zero.
    from app.core.database import get_db
    from app.models.user import User
    database = client.app.dependency_overrides[get_db]()
    db = next(database)
    uid = int(jwt.decode(first, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])['sub'])
    db.get(User, uid).session_version = 0
    db.commit()
    database.close()
    first = client.post('/api/v1/auth/login', json={'email': 'password-test@example.com', 'password': OLD}).json()['access_token']
    second = client.post('/api/v1/auth/login', json={'email': 'password-test@example.com', 'password': OLD}).json()['access_token']
    payload = jwt.decode(first, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    payload.pop('sv')
    legacy = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    assert client.get('/api/v1/auth/me', headers=headers(legacy)).status_code == 200
    changed = client.post('/api/v1/auth/change-password', headers=headers(first), json={'current_password': OLD, 'new_password': NEW})
    assert changed.status_code == 200
    assert 'hashed_password' not in changed.json()['user']
    for token in (first, second, legacy):
        assert client.get('/api/v1/auth/me', headers=headers(token)).status_code == 401
    fresh = changed.json()['access_token']
    assert client.get('/api/v1/auth/me', headers=headers(fresh)).status_code == 200
    assert client.post('/api/v1/auth/login', json={'email': 'password-test@example.com', 'password': OLD}).status_code == 401
    assert client.post('/api/v1/auth/login', json={'email': 'password-test@example.com', 'password': NEW}).status_code == 200
    assert client.post('/api/v1/auth/logout', headers=headers(fresh)).status_code == 204
    assert client.get('/api/v1/auth/me', headers=headers(fresh)).status_code == 401


@pytest.mark.parametrize('current,new,status', [('incorrect', NEW, 400), (OLD, OLD, 400), (OLD, 'short', 422)])
def test_rejected_changes_preserve_session(application_client, current, new, status):
    token = account(application_client)
    response = application_client.post('/api/v1/auth/change-password', headers=headers(token), json={'current_password': current, 'new_password': new})
    assert response.status_code == status
    assert application_client.get('/api/v1/auth/me', headers=headers(token)).status_code == 200


def test_password_attempts_are_limited(application_client):
    token = account(application_client)
    for _ in range(5):
        assert application_client.post('/api/v1/auth/change-password', headers=headers(token), json={'current_password': 'incorrect', 'new_password': NEW}).status_code == 400
    response = application_client.post('/api/v1/auth/change-password', headers=headers(token), json={'current_password': OLD, 'new_password': NEW})
    assert response.status_code == 429
    assert response.headers['Retry-After'] == '60'


def test_password_change_requires_login(application_client):
    assert application_client.post('/api/v1/auth/change-password', json={'current_password': OLD, 'new_password': NEW}).status_code == 401


@pytest.mark.parametrize('version', [True, '0', -1, 1])
def test_invalid_session_versions_are_rejected(application_client, version):
    token = account(application_client)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    payload['sv'] = version
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    assert application_client.get('/api/v1/auth/me', headers=headers(token)).status_code == 401


def test_login_racing_password_change_cannot_get_new_session_version(queue_db, monkeypatch):
    from app.api.v1 import auth
    from app.models.user import User
    from app.schemas import UserLogin
    factory, uid, _ = queue_db
    with factory() as db:
        db.get(User, uid).hashed_password = auth.get_password_hash(OLD)
        db.commit()
    original = auth.verify_password
    def verify(password, hashed):
        result = original(password, hashed)
        with factory() as writer:
            user = writer.get(User, uid)
            user.hashed_password = auth.get_password_hash(NEW)
            user.session_version = 1
            writer.commit()
        return result
    monkeypatch.setattr(auth, 'verify_password', verify)
    with factory() as db:
        response = auth.login(UserLogin(email='queue@example.com', password=OLD), db)
    payload = jwt.decode(response.access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload['sv'] == 0


def test_simultaneous_password_changes_have_one_winner(queue_db, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from fastapi import HTTPException
    from app.api.v1 import auth
    from app.models.user import User
    from app.schemas import PasswordChange
    factory, uid, _ = queue_db
    with factory() as db:
        db.get(User, uid).hashed_password = auth.get_password_hash(OLD)
        db.commit()
    barrier = Barrier(2)
    original = auth.verify_password
    def verify(password, hashed):
        result = original(password, hashed)
        barrier.wait(timeout=10)
        return result
    monkeypatch.setattr(auth, 'verify_password', verify)
    def change(suffix):
        with factory() as db:
            user = db.get(User, uid)
            try:
                auth.change_password(PasswordChange(current_password=OLD, new_password=NEW + suffix), user, db)
                return 200
            except HTTPException as exc:
                return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(change, ['A', 'B'])) == [200, 409]
    with factory() as db:
        assert db.get(User, uid).session_version == 1

from concurrent.futures import ThreadPoolExecutor
from threading import Event
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from app.core.database import get_db
from app.deps import get_current_user
from app.api.v1 import interview
from app.models.user import User
from app.models.interview import InterviewSession, InterviewEvaluation
from app.services import InterviewService
from app.services.interview_service import ai_router_engine
from test_reliability import queue_db

RESULT = dict(score=80,strengths=['Clear'],mistakes=['Add evidence'],suggested_answer='template',next_question='Next question')

def make_client(factory,uid):
    app=FastAPI();app.include_router(interview.router,prefix='/api/v1')
    def db_dep():
        with factory() as db: yield db
    def user_dep():
        with factory() as db: return db.get(User,uid)
    # Simulate separate workers: bypass the process-local guard to exercise the DB claim.
    app.dependency_overrides[interview.expensive_request]=lambda: None
    app.dependency_overrides[get_db]=db_dep;app.dependency_overrides[get_current_user]=user_dep
    return TestClient(app)

def seed(queue_db):
    factory,uid,rid=queue_db
    with factory() as db:
        row=InterviewSession(user_id=uid,resume_session_id=rid,target_role='Teacher',interview_type='Mixed',history=[dict(question='Question',answer=None,evaluation=None)])
        db.add(row);db.commit();sid=row.id
    return factory,uid,sid

def payload(sid,answer='My actual experience'):
    return dict(session_id=sid,question_index=0,question='Question',user_answer=answer)

def test_concurrent_answers_and_lost_response_retry(queue_db,monkeypatch):
    factory,uid,sid=seed(queue_db); entered=Event();release=Event()
    def provider(*args): entered.set();assert release.wait(30);return RESULT.copy()
    mock=Mock(side_effect=provider);monkeypatch.setattr(InterviewService,'evaluate_response',mock)
    def submit():
        with make_client(factory,uid) as api:return api.post('/api/v1/interview/evaluate',json=payload(sid))
    with ThreadPoolExecutor(2) as pool:
        pending=pool.submit(submit)
        try:
            assert entered.wait(10)
            with make_client(factory,uid) as api:
                assert api.post('/api/v1/interview/evaluate',json=payload(sid)).status_code==409
                assert api.post('/api/v1/interview/evaluate',json=payload(sid,'Conflicting answer')).status_code==409
        finally: release.set()
        first=pending.result();assert first.status_code==200,first.text
    with make_client(factory,uid) as api:
        retry=api.post('/api/v1/interview/evaluate',json=payload(sid))
        assert retry.json()==first.json()
        assert api.post('/api/v1/interview/evaluate',json=payload(sid,'Conflicting answer')).status_code==409
        restored=api.get(f'/api/v1/interview/sessions/{sid}').json()
        assert len(restored['history'])==2
        assert restored['history'][0]['answer']=='My actual experience'
        assert api.get('/api/v1/interview/sessions').json()[0]['id']==sid
    assert mock.call_count==1

def test_provider_failure_releases_claim_for_retry(queue_db,monkeypatch):
    factory,uid,sid=seed(queue_db)
    mock=Mock(side_effect=[HTTPException(503,'Provider timeout'),RESULT.copy()]);monkeypatch.setattr(InterviewService,'evaluate_response',mock)
    with make_client(factory,uid) as api:
        assert api.post('/api/v1/interview/evaluate',json=payload(sid)).status_code==503
        assert api.post('/api/v1/interview/evaluate',json=payload(sid,'Corrected answer')).status_code==200
    assert mock.call_count==2

def test_expired_worker_cannot_overwrite_replacement(queue_db,monkeypatch):
    factory,uid,sid=seed(queue_db);entered=Event();release=Event();calls=[]
    def provider(*args):
        calls.append(1)
        if len(calls)==1: entered.set();assert release.wait(30)
        return RESULT.copy()
    monkeypatch.setattr(InterviewService,'evaluate_response',provider)
    def submit():
        with make_client(factory,uid) as api:return api.post('/api/v1/interview/evaluate',json=payload(sid))
    with ThreadPoolExecutor(2) as pool:
        old=pool.submit(submit)
        try:
            assert entered.wait(10)
            with factory() as db:
                attempt=db.get(InterviewEvaluation,(sid,0));attempt.expires_at=datetime.now(timezone.utc).replace(tzinfo=None)-timedelta(seconds=1);db.commit()
            with make_client(factory,uid) as api:
                replacement=api.post('/api/v1/interview/evaluate',json=payload(sid,'Replacement answer'));assert replacement.status_code==200,replacement.text
        finally: release.set()
        assert old.result().status_code==409
    with factory() as db: assert db.get(InterviewSession,sid).history[0]['answer']=='Replacement answer'

def test_recovery_and_evaluation_are_owned(queue_db):
    factory,uid,sid=seed(queue_db)
    with factory() as db:
        other=User(email='other@example.com',hashed_password='test');db.add(other);db.commit();oid=other.id
    with make_client(factory,oid) as api:
        assert api.get('/api/v1/interview/sessions').json()==[]
        assert api.get(f'/api/v1/interview/sessions/{sid}').status_code==404
        assert api.post('/api/v1/interview/evaluate',json=payload(sid)).status_code==404

def test_provider_biography_is_replaced_by_fact_safe_template(monkeypatch):
    monkeypatch.setattr(ai_router_engine,'generate_json',lambda *args:{**RESULT,'suggested_answer':'I worked at Imaginary Hospital and increased outcomes 90%.'})
    result=InterviewService.evaluate_response('Mixed','Nurse','Question','I completed supervised placements.')
    assert 'Imaginary Hospital' not in result['suggested_answer']
    assert '90%' not in result['suggested_answer']
    assert 'I completed supervised placements.' in result['suggested_answer']
    assert '[your actual situation' in result['suggested_answer']


def test_repeated_question_text_uses_index_and_legacy_examples_are_sanitized(queue_db,monkeypatch):
    factory,uid,sid=seed(queue_db)
    monkeypatch.setattr(InterviewService,'evaluate_response',lambda *args:{**RESULT,'next_question':'Question'})
    with make_client(factory,uid) as api:
        first=api.post('/api/v1/interview/evaluate',json=payload(sid));assert first.status_code==200
        second={**payload(sid,'Second answer'),'question_index':1}
        assert api.post('/api/v1/interview/evaluate',json=second).status_code==200
        assert api.post('/api/v1/interview/evaluate',json=payload(sid)).json()==first.json()
    with factory() as db:
        session=db.get(InterviewSession,sid)
        session.history=[{'question':'Old question','answer':'Real answer','evaluation':{**RESULT,'suggested_answer':'I invented 90% improvement'}}]
        db.commit()
    with make_client(factory,uid) as api:
        answer=api.get(f'/api/v1/interview/sessions/{sid}').json()['history'][0]['evaluation']['suggested_answer']
        assert '90%' not in answer and 'Real answer' in answer

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import Mock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.deps import get_current_user
from app.core.config import settings
from app.core.request_limits import RequestLimitsMiddleware, client_identity
from app.models import User, ResumeSession, CareerReport
from app.models.research import ResearchJob, ResearchLease, ResearchSlot
from app.services import research_worker as worker
from app.api.v1 import reports
from test_security_regressions import secured, account


def test_trusted_proxy_chain_and_spoofing(monkeypatch):
    scope = {'client': ('127.0.0.1', 12), 'headers': [(b'x-forwarded-for', b'9.9.9.9, 203.0.113.1, 10.1.1.1')]}
    monkeypatch.setattr(settings, 'TRUSTED_PROXY_CIDRS', [])
    assert client_identity(scope) == '127.0.0.1'
    monkeypatch.setattr(settings, 'TRUSTED_PROXY_CIDRS', ['127.0.0.0/8','10.0.0.0/8'])
    assert client_identity(scope) == '203.0.113.1'
    scope['client'] = ('198.51.100.2', 1)
    assert client_identity(scope) == '198.51.100.2'


def test_loopback_accounts_do_not_share_small_budget():
    app=FastAPI();app.add_middleware(RequestLimitsMiddleware, auth_limit=2)
    @app.post('/api/v1/auth/login')
    def login():return {}
    with TestClient(app, client=('127.0.0.1', 123)) as client:
        for i in range(10): assert client.post('/api/v1/auth/login',json={'email':'one@example.com'}).status_code==200
        assert client.post('/api/v1/auth/login',json={'email':'one@example.com'},headers={'X-Forwarded-For':'8.8.8.8'}).status_code==429
        assert client.post('/api/v1/auth/login',json={'email':'two@example.com'}).status_code==200


@pytest.fixture
def queue_db(tmp_path, monkeypatch):
    import os
    from sqlalchemy import text
    from app.core.migrations import migrate
    url=os.getenv('POSTGRES_TEST_URL')
    engine=create_engine(url) if url else create_engine('sqlite:///'+str(tmp_path/'queue.db'),connect_args={'check_same_thread':False,'timeout':5})
    if url:
        assert engine.url.database == 'careermind_test', 'Refusing a non-test database'
        with engine.begin() as connection:
            connection.execute(text('DROP SCHEMA public CASCADE'))
            connection.execute(text('CREATE SCHEMA public'))
    migrate(engine); factory=sessionmaker(bind=engine)
    monkeypatch.setattr(worker,'SessionLocal',factory)
    with factory() as db:
        user=User(email='queue@example.com',hashed_password='test');db.add(user);db.flush()
        resume=ResumeSession(user_id=user.id,session_uuid='sample',file_name='resume.docx',file_type='.docx',file_path='unused',raw_text='Python SQL',parsed_data={});db.add(resume);db.commit()
        uid,rid=user.id,resume.id
    yield factory,uid,rid
    engine.dispose()


def payload(rid):
    return {'resume_id':rid,'job_role':'Backend Developer','location':'Worldwide','experience_level':'Junior','search_market':False,'job_description':'Python and SQL skills are required. Build backend APIs, write tests, and collaborate with the engineering team.'}


def client_for(factory,uid):
    app=FastAPI();app.include_router(reports.router,prefix='/api/v1')
    def db_dep():
        with factory() as db:yield db
    def user_dep():
        with factory() as db:return db.get(User,uid)
    app.dependency_overrides[get_db]=db_dep;app.dependency_overrides[get_current_user]=user_dep
    return TestClient(app)


def test_concurrent_idempotent_admission(queue_db):
    factory,uid,rid=queue_db
    def post(_):
        with client_for(factory,uid) as client:return client.post('/api/v1/analysis/research',json=payload(rid),headers={'Idempotency-Key':'same-key'})
    with ThreadPoolExecutor(max_workers=4) as pool: results=list(pool.map(post,range(4)))
    assert all(r.status_code==202 for r in results),[(r.status_code,r.text) for r in results]
    assert len({r.json()['id'] for r in results})==1
    with factory() as db:assert db.query(ResearchJob).count()==1
    with client_for(factory,uid) as client:
        assert client.post('/api/v1/analysis/research',json={**payload(rid),'job_role':'Designer'},headers={'Idempotency-Key':'same-key'}).status_code==409
        assert client.post('/api/v1/analysis/research',json=payload(rid),headers={'Idempotency-Key':'new-key'}).status_code==409


def test_worker_restart_recovery_and_single_report(queue_db,monkeypatch):
    factory,uid,rid=queue_db
    with client_for(factory,uid) as client:jobid=client.post('/api/v1/analysis/research',json=payload(rid)).json()['id']
    with factory() as db:
        assert worker.claim(db,jobid,'dead-process')
        db.get(ResearchLease,jobid).expires_at=worker.now()-timedelta(seconds=1);db.commit()
    with factory() as db:worker.maintain_queue(db)
    mock=Mock(return_value=({'match_percent':50,'matched_skills':['Python']},{'missing_skills':['SQL']}));monkeypatch.setattr(worker,'research',mock)
    worker.run_research(jobid);worker.run_research(jobid)
    with factory() as db:
        assert db.get(ResearchJob,jobid).status=='completed'
        assert db.query(CareerReport).count()==1
        assert db.get(ResearchSlot,uid).job_id is None
        assert db.get(ResearchLease,jobid).attempts==2
    assert mock.call_count==1


def test_saturation_keeps_job_queued(queue_db,monkeypatch):
    factory,uid,rid=queue_db
    with client_for(factory,uid) as client:jobid=client.post('/api/v1/analysis/research',json=payload(rid)).json()['id']
    monkeypatch.setattr(worker,'_capacity',Mock(acquire=Mock(return_value=False)))
    worker.run_research(jobid)
    with factory() as db:assert db.get(ResearchJob,jobid).status=='pending'


def test_settings_cannot_save_unused_model(secured):
    client,db=secured;_,headers=account(client)
    assert client.get('/api/v1/user/settings',headers=headers).json()['preferred_ai_model']==settings.OLLAMA_MODEL
    assert client.put('/api/v1/user/settings',headers=headers,json={'preferred_ai_model':'invented'}).status_code==422


def test_history_is_bounded_and_private(secured):
    client,db=secured;uid,headers=account(client)
    resume=ResumeSession(user_id=uid,session_uuid='pagination',file_name='r.docx',file_type='.docx',file_path='unused',parsed_data={});db.add(resume);db.flush()
    for i in range(60):db.add(CareerReport(user_id=uid,resume_session_id=resume.id,field='test',job_role='Role '+str(i),experience_level='Junior',analysis_data={'match_percent':0,'evidence':'x'*10000},ats_score=90))
    db.commit()
    full=client.get('/api/v1/analysis/reports?limit=50',headers=headers);summary=client.get('/api/v1/analysis/report-summaries?limit=50',headers=headers)
    assert len(full.json())==50 and len(summary.json()['items'])==50
    assert len(summary.content)<len(full.content)/20
    print(json.dumps({'fixture_reports':60,'page_reports':50,'full_report_bytes':len(full.content),'summary_bytes':len(summary.content)}))
    assert full.json()[0]['ats_score'] is None and full.json()[0]['nex_score']==0
    cursor=summary.json()['next_before'];older=client.get(f'/api/v1/analysis/report-summaries?before={cursor}',headers=headers).json()
    assert len(older['items'])==10
    assert client.get('/api/v1/analysis/reports?limit=1000',headers=headers).status_code==422
    _,other=account(client,'other-pagination@example.com')
    assert client.get('/api/v1/analysis/reports/'+str(full.json()[0]['id']),headers=other).status_code==404


def test_backup_restore_and_path_validation(tmp_path):
    import importlib.util
    from pathlib import Path
    import sqlite3, zipfile, hashlib
    spec=importlib.util.spec_from_file_location('storage_backup',Path(__file__).parents[1]/'scripts/storage_backup.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    source=tmp_path/'source.db'
    with sqlite3.connect(source) as db:db.execute('CREATE TABLE sample (id INTEGER)');db.execute('INSERT INTO sample VALUES (7)')
    uploads=tmp_path/'uploads';uploads.mkdir();(uploads/'resume.txt').write_text('synthetic resume')
    archive=tmp_path/'backup.zip';module.backup(source,uploads,archive)
    target=tmp_path/'restored';module.restore(archive,target)
    with sqlite3.connect(target/'database.sqlite') as db:assert db.execute('SELECT id FROM sample').fetchone()[0]==7
    assert (target/'uploads/resume.txt').read_text()=='synthetic resume'
    with pytest.raises(ValueError):module.restore(archive,target)
    malicious=tmp_path/'malicious.zip'
    with zipfile.ZipFile(malicious,'w') as bundle:
        bundle.writestr('../escape','bad');bundle.writestr('manifest.json',json.dumps({'../escape':hashlib.sha256(b'bad').hexdigest()}))
    with pytest.raises(ValueError,match='Unsafe'):module.restore(malicious,tmp_path/'safe')
    assert not (tmp_path/'escape').exists()


def test_hourly_budget_and_readiness(secured, monkeypatch):
    client,db=secured;uid,headers=account(client)
    resume=ResumeSession(user_id=uid,session_uuid='quota',file_name='r.docx',file_type='.docx',file_path='unused',parsed_data={});db.add(resume);db.flush()
    for i in range(12):db.add(ResearchJob(user_id=uid,status='failed',request_data={}))
    db.commit()
    assert client.post('/api/v1/analysis/research',headers=headers,json=payload(resume.id)).status_code==429
    from app.api import router as module
    # Import the module explicitly: app.api also exports api_router.
    import importlib
    module=importlib.import_module('app.api.router')
    monkeypatch.setattr(module,'engine',Mock(connect=Mock(side_effect=RuntimeError('private connection info'))))
    response=module.readiness()
    assert response.status_code==503 and b'private' not in response.body


def test_distinct_trusted_clients_have_independent_limits(monkeypatch):
    monkeypatch.setattr(settings,'TRUSTED_PROXY_CIDRS',['127.0.0.0/8'])
    app=FastAPI();app.add_middleware(RequestLimitsMiddleware,auth_limit=2)
    @app.post('/api/v1/auth/login')
    def login():return {}
    with TestClient(app,client=('127.0.0.1',123)) as client:
        for i in range(2):assert client.post('/api/v1/auth/login',headers={'X-Forwarded-For':f'8.8.8.{i}, 203.0.113.1'},json={'email':f'a{i}@example.com'}).status_code==200
        assert client.post('/api/v1/auth/login',headers={'X-Forwarded-For':'9.9.9.9, 203.0.113.1'},json={'email':'another@example.com'}).status_code==429
        assert client.post('/api/v1/auth/login',headers={'X-Forwarded-For':'203.0.113.2'},json={'email':'different@example.com'}).status_code==200

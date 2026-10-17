import pytest
from pydantic import ValidationError
from app.schemas import ResearchRequest, StartInterviewRequest
from app.api.v1.settings import SettingsUpdate
from app.intelligence.career_engine import career_engine
from app.models.research import ResearchJob
from test_reliability import queue_db, client_for, payload
from test_career_flow import client

@pytest.mark.parametrize('role', ['Registered Nurse', 'Chartered Accountant', 'School Teacher', 'Electrician', 'Architect', 'वित्त सलाहकार'])
def test_arbitrary_roles_reach_research_queue(queue_db, role):
    factory, uid, rid = queue_db
    with client_for(factory, uid) as api:
        response = api.post('/api/v1/analysis/research', json={**payload(rid), 'job_role': role})
    assert response.status_code == 202
    with factory() as db:
        assert db.get(ResearchJob, response.json()['id']).request_data['job_role'] == role
    assert SettingsUpdate(target_job_role=role).target_job_role == role
    assert StartInterviewRequest(target_role=role).target_role == role

@pytest.mark.parametrize('schema,field', [(SettingsUpdate,'target_job_role'),(StartInterviewRequest,'target_role')])
def test_role_whitespace_is_not_a_profession(schema,field):
    with pytest.raises(ValidationError): schema(**{field:'   '})
    assert getattr(schema(**{field:'  Nurse  '}),field) == 'Nurse'

def test_unknown_profession_never_gets_software_requirements():
    with pytest.raises(ValueError, match='evidence-based'):
        career_engine.evaluate_candidate(['Nursing'], 'Registered Nurse')

def test_legacy_upload_rejects_unknown_profile_before_saving(client, monkeypatch):
    from app.api.v1 import resume
    api, db, user = client
    def unexpected(*args): raise AssertionError('Must not persist an upload before role validation')
    monkeypatch.setattr(resume, 'save_resume_upload', unexpected)
    response = api.post('/api/v1/resume/auto-pipeline?target_role=Registered%20Nurse', files={'file':('resume.docx',b'disposable')})
    assert response.status_code == 422
    assert '/api/v1/analysis/research' in response.json()['detail']


def test_nursing_match_uses_source_requirements_and_resume_evidence(monkeypatch):
    from app.services import job_research as research
    description = 'Registered Nurse in London. Patient assessment required. Active local registration required. Ward teamwork preferred.'
    resume = 'Completed patient assessment and ward teamwork during supervised clinical placements.'
    job = research.ExtractedJob.model_validate(dict(source_id=0, is_job_posting=True,
        title='Registered Nurse', title_quote='Registered Nurse', company='Example Hospital', location='London',
        role_match=True, location_match=True, level_match=True, comparison_reason='Nursing role in London',
        comparison_quote='Registered Nurse in London', closed=False, requirements=[
            dict(name='Patient assessment',kind='skill',importance='required',source_quote='Patient assessment required',resume_status='evidenced',resume_quote='patient assessment'),
            dict(name='Active local registration',kind='qualification',importance='required',source_quote='Active local registration required',resume_status='not_found',resume_quote='')]))
    monkeypatch.setattr(research, 'extract', lambda *args: research.Extraction(jobs=[job]))
    req = ResearchRequest(resume_id=1,job_role='Registered Nurse',location='London',experience_level='Junior',search_market=False,job_description=description)
    analysis, gap = research.research(req, resume)
    match = analysis['research']['company_match']
    assert match['coverage'] == 50
    assert {item['name'] for item in match['requirements']} == {'Patient assessment','Active local registration'}
    assert match['requirements'][1]['resume_status'] == 'not_found'
    assert 'Python' not in str(analysis)

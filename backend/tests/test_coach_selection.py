from test_career_flow import client
from app.models.session import ResumeSession
from app.models.report import CareerReport
from app.models.user import User
from app.services.coach_service import CoachService


def test_explicit_report_controls_context_messages_history_and_clear(client,monkeypatch):
    api,db,user=client
    resume=ResumeSession(user_id=user.id,session_uuid='coach-choice',file_name='sample.docx',file_type='.docx',file_path='unused',raw_text='Experience',parsed_data={})
    db.add(resume);db.flush()
    def report(uid,role):
        row=CareerReport(user_id=uid,resume_session_id=resume.id,field='Professional',job_role=role,experience_level='Junior',analysis_data={},gap_analysis={});db.add(row);db.flush();return row.id
    first=report(user.id,'Teacher');second=report(user.id,'Nurse')
    other=User(email='other@example.com',hashed_password='test');db.add(other);db.flush();foreign=report(other.id,'Private role');db.commit()
    monkeypatch.setattr(CoachService,'generate_coach_response',lambda db,query,session,report:report.job_role)
    assert api.get(f'/api/v1/chat/context?report_id={first}').json()['job_role']=='Teacher'
    for rid in [first,second]:
        assert api.post('/api/v1/chat/message',json={'content':'Help me','report_id':rid}).status_code==200
    assert api.get(f'/api/v1/chat/history?report_id={first}').json()['messages'][-1]['content']=='Teacher'
    assert api.delete(f'/api/v1/chat/clear?report_id={first}').status_code==204
    assert api.get(f'/api/v1/chat/history?report_id={first}').json()['messages']==[]
    assert len(api.get(f'/api/v1/chat/history?report_id={second}').json()['messages'])==2
    for route in ['context','history']:
        assert api.get(f'/api/v1/chat/{route}?report_id={foreign}').status_code==404
    assert api.delete(f'/api/v1/chat/clear?report_id={foreign}').status_code==404
    assert api.post('/api/v1/chat/message',json={'content':'Help','report_id':foreign}).status_code==404

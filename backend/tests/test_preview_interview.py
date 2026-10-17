from test_security_regressions import secured, account
from app.models.session import ResumeSession
from app.models.interview import InterviewSession
from app.services import InterviewService


def test_resume_text_is_private_and_not_in_list(secured):
    client, db = secured
    uid, headers = account(client)
    _, other = account(client, 'other@example.com')
    record = ResumeSession(user_id=uid, session_uuid='preview', file_name='nurse.docx', file_type='.docx', file_path='unused', raw_text='Private clinical education and experience', parsed_data={})
    db.add(record); db.commit()
    url=f'/api/v1/resume/session/{record.id}/text'
    assert client.get(url).status_code == 401
    assert client.get(url,headers=other).status_code == 404
    response=client.get(url,headers=headers)
    assert response.status_code == 200
    assert response.json()['text'] == record.raw_text
    assert response.headers['cache-control'] == 'no-store'
    assert 'raw_text' not in client.get('/api/v1/resume/my-resumes',headers=headers).json()[0]
    assert client.get('/api/v1/resume/session/99999/text',headers=headers).status_code == 404


def test_last_interview_answer_has_no_phantom_next_question(secured,monkeypatch):
    client, db = secured
    uid, headers = account(client)
    history=[{'question':f'Question {i}', 'answer':'Answer', 'evaluation':{'score':50}} for i in range(19)]
    history.append({'question':'Last question','answer':None,'evaluation':None})
    record=InterviewSession(user_id=uid,interview_type='Mixed',target_role='Teacher',overall_score=0,history=history)
    db.add(record);db.commit()
    monkeypatch.setattr(InterviewService,'evaluate_response',lambda *args: {'score':80,'strengths':['Clear'],'mistakes':[],'suggested_answer':'Example','next_question':'Do not expose question 21'})
    payload={'session_id':record.id,'question':'Last question','user_answer':'My answer'}
    response=client.post('/api/v1/interview/evaluate',headers=headers,json=payload)
    assert response.status_code==200
    assert response.json()['next_question'] is None
    db.refresh(record)
    assert len(record.history)==20
    assert record.history[-1]['answer']=='My answer'
    assert client.post('/api/v1/interview/evaluate',headers=headers,json=payload).status_code==409

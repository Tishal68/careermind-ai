from io import BytesIO
from pathlib import Path
from unittest.mock import Mock

import docx
import pytest
from fastapi import UploadFile
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from test_career_flow import client
from app.api.v1 import resume
from app.core.migrations import migrate
from app.models import User, ResumeSession


def document_bytes():
    document = docx.Document()
    document.add_paragraph('Registered nurse with supervised clinical experience.')
    stream = BytesIO()
    document.save(stream)
    return stream.getvalue()


def test_upload_download_private_and_delete(client):
    api, db, user = client
    content = document_bytes()
    created = api.post('/api/v1/resume/upload', files={'file':('nurse.docx', content)})
    assert created.status_code == 201, created.text
    rid = created.json()['id']
    assert 'file_content' not in created.json()
    record = db.get(ResumeSession, rid)
    assert record.file_path == ''
    db.expire_all()
    assert 'file_content' in inspect(db.get(ResumeSession, rid)).unloaded
    downloaded = api.get(f'/api/v1/resume/session/{rid}/file')
    assert downloaded.content == content
    assert downloaded.headers['cache-control'] == 'no-store'
    assert downloaded.headers['content-disposition'].startswith('attachment;')
    assert not list(Path(resume.UPLOAD_DIR).rglob('*.docx'))
    other = User(email='foreign@example.com', hashed_password='test')
    db.add(other); db.flush()
    foreign = ResumeSession(user_id=other.id, file_name='private.pdf', file_type='.pdf',
        file_path='', file_content=b'private')
    db.add(foreign); db.commit()
    assert api.get(f'/api/v1/resume/session/{foreign.id}/file').status_code == 404
    assert api.delete(f'/api/v1/resume/session/{rid}').status_code == 204
    assert api.get(f'/api/v1/resume/session/{rid}/file').status_code == 404


def test_original_survives_reopening_database_without_local_uploads(tmp_path, monkeypatch):
    monkeypatch.setattr(resume, 'UPLOAD_DIR', str(tmp_path/'uploads'))
    url = 'sqlite:///' + str(tmp_path/'persistent.db')
    engine = create_engine(url)
    migrate(engine)
    content = document_bytes()
    with Session(engine) as db:
        user = User(email='persist@example.com', hashed_password='test')
        db.add(user); db.commit()
        record = resume.persist_resume_upload(UploadFile(file=BytesIO(content), filename='nurse.docx'), user.id, db)
        rid = record.id
    engine.dispose()
    reopened = create_engine(url)
    with Session(reopened) as db:
        record = db.get(ResumeSession, rid)
        assert record.file_content == content
        assert 'Registered nurse' in record.raw_text
        assert not list((tmp_path/'uploads').rglob('*.docx'))
    reopened.dispose()


def test_failed_commit_does_not_leave_local_resume(client, monkeypatch):
    _, db, user = client
    monkeypatch.setattr(db, 'commit', Mock(side_effect=RuntimeError('database unavailable')))
    with pytest.raises(RuntimeError, match='database unavailable'):
        resume.persist_resume_upload(UploadFile(file=BytesIO(document_bytes()), filename='nurse.docx'), user.id, db)
    assert db.query(ResumeSession).count() == 0
    assert not list(Path(resume.UPLOAD_DIR).rglob('*.docx'))

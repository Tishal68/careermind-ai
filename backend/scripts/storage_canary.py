"""Synthetic persistence check for disposable production-container CI only."""
import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.config import settings
from app.core.database import SessionLocal
from app.models import User, ResumeSession, CareerReport, InterviewSession

EMAIL = "storage-canary@example.invalid"
CONTENTS = b"Synthetic storage persistence canary; no personal data."


def run(mode):
    path = Path(settings.UPLOAD_DIR) / "storage-canary.txt"
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == EMAIL).one_or_none()
        if mode == "seed":
            assert user is None, "Canary already exists"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(CONTENTS)
            user = User(email=EMAIL, hashed_password="disabled-canary", is_active=False)
            db.add(user)
            db.flush()
            resume = ResumeSession(user_id=user.id, session_uuid="storage-canary", file_name=path.name,
                                   file_type=".txt", file_path=str(path), raw_text=CONTENTS.decode(), parsed_data={})
            db.add(resume)
            db.flush()
            db.add(CareerReport(user_id=user.id, resume_session_id=resume.id, field="Test", job_role="Teacher",
                               experience_level="Junior", analysis_data={"canary": True}))
            db.add(InterviewSession(user_id=user.id, resume_session_id=resume.id, target_role="Teacher",
                                    interview_type="Mixed", history=[{"question": "Canary", "answer": "Saved"}]))
            db.commit()
        else:
            assert user is not None and user.is_active is False
            resume = db.query(ResumeSession).filter_by(user_id=user.id).one()
            assert resume.session_uuid == "storage-canary" and Path(resume.file_path) == path
            assert db.query(CareerReport).filter_by(user_id=user.id).one().analysis_data == {"canary": True}
            assert db.query(InterviewSession).filter_by(user_id=user.id).one().history[0]["answer"] == "Saved"
            assert hashlib.sha256(path.read_bytes()).digest() == hashlib.sha256(CONTENTS).digest()
    print("Synthetic persistence canary " + mode + " passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["seed", "verify"])
    run(parser.parse_args().mode)

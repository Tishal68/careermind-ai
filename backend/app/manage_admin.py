"""Usage: python -m app.manage_admin registered-email@example.com"""
import argparse
from app.core.database import SessionLocal
from app.models.user import User

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grant admin access to one existing active account.")
    parser.add_argument("email")
    args = parser.parse_args()
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == args.email).first()
        if not user or not user.is_active:
            parser.error("Register a personal active account first. Disabled accounts cannot be promoted.")
        user.is_superuser = True
        db.commit()
        print("Administrator access granted to the specified account.")

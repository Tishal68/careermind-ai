"""Normalize existing user emails to canonical lowercase after detecting collisions."""
from alembic import op
import sqlalchemy as sa

revision = "0003_normalize_user_emails"
down_revision = "0002_session_version"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    # 1. Detect existing case-colliding accounts before migration
    collision_check = connection.execute(
        sa.text(
            "SELECT LOWER(email) AS norm_email, COUNT(*) AS cnt "
            "FROM users GROUP BY LOWER(email) HAVING COUNT(*) > 1"
        )
    ).fetchall()

    if collision_check:
        colliding = [row[0] for row in collision_check]
        raise RuntimeError(
            f"Existing case-colliding accounts detected: {colliding}. "
            "Do not silently merge accounts. Resolve colliding accounts before running this migration."
        )

    # 2. Normalize existing emails to canonical lowercase
    connection.execute(sa.text("UPDATE users SET email = LOWER(email) WHERE email != LOWER(email)"))


def downgrade():
    raise RuntimeError("Cannot revert email normalization; case information is intentionally canonicalized.")

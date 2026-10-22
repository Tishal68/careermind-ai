"""Invalidate all previous sessions when a password changes."""
from alembic import op
import sqlalchemy as sa

revision = "0002_session_version"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("session_version", sa.Integer(), nullable=False, server_default="0"))


def downgrade():
    raise RuntimeError("Removing session revocation can reactivate old tokens; restore a reviewed backup instead.")

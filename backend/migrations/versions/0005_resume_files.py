"""Persist original resumes with their database record."""
from alembic import op
import sqlalchemy as sa

revision = "0005_resume_files"
down_revision = "0004_account_lifecycle"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("resume_sessions", sa.Column("file_content", sa.LargeBinary(), nullable=True))


def downgrade():
    op.drop_column("resume_sessions", "file_content")

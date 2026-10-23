"""Add account_tokens table and is_verified column to users."""
from alembic import op
import sqlalchemy as sa


revision = "0004_account_tokens_and_lifecycle"
down_revision = "0003_normalize_user_emails"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), server_default="0", nullable=False))
    op.create_table(
        "account_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("token_type", sa.String(32), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_account_tokens_id", "account_tokens", ["id"])
    op.create_index("ix_account_tokens_user_id", "account_tokens", ["user_id"])
    op.create_index("ix_account_tokens_token_hash", "account_tokens", ["token_hash"], unique=True)
    op.create_index("ix_account_tokens_token_type", "account_tokens", ["token_type"])
    op.create_index("ix_account_tokens_expires_at", "account_tokens", ["expires_at"])


def downgrade():
    op.drop_index("ix_account_tokens_expires_at", table_name="account_tokens")
    op.drop_index("ix_account_tokens_token_type", table_name="account_tokens")
    op.drop_index("ix_account_tokens_token_hash", table_name="account_tokens")
    op.drop_index("ix_account_tokens_user_id", table_name="account_tokens")
    op.drop_index("ix_account_tokens_id", table_name="account_tokens")
    op.drop_table("account_tokens")
    op.drop_column("users", "is_verified")

"""Ánh xạ tài khoản nghiệp vụ sang Supabase Auth mà không mất dữ liệu cũ.

Revision ID: 0002_supabase_auth_mapping
Revises: 0001_initial_auth
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_supabase_auth_mapping"
down_revision: str | None = "0001_initial_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("auth_user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.alter_column("users", "credential_reference", existing_type=sa.Text(), nullable=True)
    op.create_index("ix_users_auth_user_id", "users", ["auth_user_id"], unique=True)
    op.create_foreign_key(
        "fk_users_auth_user_id",
        "users",
        "users",
        ["auth_user_id"],
        ["id"],
        source_schema=None,
        referent_schema="auth",
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_users_auth_user_id", "users", type_="foreignkey")
    op.drop_index("ix_users_auth_user_id", table_name="users")
    op.drop_column("users", "auth_user_id")
    op.alter_column("users", "credential_reference", existing_type=sa.Text(), nullable=False)

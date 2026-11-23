"""Baseline tương đương migration EF InitialAuth.

Revision ID: 0001_initial_auth
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_auth"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.SmallInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_roles"),
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)
    op.bulk_insert(
        sa.table("roles", sa.column("id", sa.SmallInteger()), sa.column("name", sa.Text())),
        [
            {"id": 1, "name": "Quản trị viên"},
            {"id": 2, "name": "Sinh viên/Gia sư"},
            {"id": 3, "name": "Phụ huynh"},
        ],
    )
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", sa.SmallInteger(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("login_identifier", sa.Text(), nullable=False),
        sa.Column("credential_reference", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("token_version", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name="fk_users_roles_role_id", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )
    op.create_index("ix_users_login_identifier", "users", ["login_identifier"], unique=True)
    op.create_index("ix_users_role_id", "users", ["role_id"], unique=False)


def downgrade() -> None:
    op.drop_table("users")
    op.drop_table("roles")

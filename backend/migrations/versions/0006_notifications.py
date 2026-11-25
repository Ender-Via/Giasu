"""Bảng thông báo trong ứng dụng và cấu hình nhận email theo loại (FR-32).

Revision ID: 0006_notifications
Revises: 0005_auth_registration_trigger
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_notifications"
down_revision: str | None = "0005_auth_registration_trigger"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NOTIFICATION_TYPES = (
    "ModerationResult",
    "NewApplication",
    "ApplicationStatus",
    "Roadmap",
    "Session",
    "RequestExpiry",
    "Tuition",
    "Progress",
    "Violation",
    "ModerationQueue",
)


def _in_list(column: str, values: Sequence[str]) -> str:
    quoted = ", ".join("'" + value.replace("'", "''") + "'" for value in values)
    return f"{column} IN ({quoted})"


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("link", sa.Text(), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["recipient_id"],
            ["users.id"],
            name="fk_notifications_recipient_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_notifications"),
        sa.CheckConstraint(_in_list("type", NOTIFICATION_TYPES), name="ck_notifications_type"),
        sa.CheckConstraint("char_length(title) >= 1", name="ck_notifications_title"),
        sa.CheckConstraint("char_length(message) >= 1", name="ck_notifications_message"),
        sa.CheckConstraint("link IS NULL OR link LIKE '/%'", name="ck_notifications_link"),
    )
    op.create_index(
        "ix_notifications_recipient_is_read_created_at",
        "notifications",
        ["recipient_id", "is_read", "created_at"],
    )

    op.create_table(
        "notification_preferences",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("email_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_notification_preferences_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("user_id", "type", name="pk_notification_preferences"),
        sa.CheckConstraint(
            _in_list("type", NOTIFICATION_TYPES), name="ck_notification_preferences_type"
        ),
    )


def downgrade() -> None:
    op.drop_table("notification_preferences")
    op.drop_index("ix_notifications_recipient_is_read_created_at", table_name="notifications")
    op.drop_table("notifications")

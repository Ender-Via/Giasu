"""Nhật ký chuyển trạng thái (BR-22, NFR-04)."""

import sqlalchemy as sa
from alembic import op

revision = "0008_audit_logs"
down_revision = "0007_student_verifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("entity", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("from_status", sa.Text(), nullable=True),
        sa.Column("to_status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_id"], ["users.id"], name="fk_audit_logs_actor_id", ondelete="RESTRICT"
        ),
    )
    op.create_index("ix_audit_logs_entity_entity_id", "audit_logs", ["entity", "entity_id"])


def downgrade() -> None:
    op.drop_table("audit_logs")

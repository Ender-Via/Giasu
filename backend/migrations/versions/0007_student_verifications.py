"""Yêu cầu xác thực sinh viên của gia sư (FR-02, UC-18).

Revision ID: 0007_student_verifications
Revises: 0006_notifications
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_student_verifications"
down_revision: str | None = "0006_notifications"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "student_verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tutor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("university", sa.Text(), nullable=False),
        sa.Column("student_code", sa.Text(), nullable=False),
        sa.Column("evidence_file_ref", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default="Pending", nullable=False),
        sa.Column("reject_reason", sa.Text(), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tutor_id"],
            ["tutors.user_id"],
            name="fk_student_verifications_tutor_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["users.id"],
            name="fk_student_verifications_reviewed_by",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_student_verifications"),
        sa.CheckConstraint(
            "status IN ('Pending', 'Verified', 'Rejected')",
            name="ck_student_verifications_status",
        ),
        sa.CheckConstraint(
            "char_length(university) BETWEEN 2 AND 150",
            name="ck_student_verifications_university",
        ),
        sa.CheckConstraint(
            "char_length(student_code) BETWEEN 3 AND 20 AND student_code ~ '^[A-Za-z0-9]+$'",
            name="ck_student_verifications_student_code",
        ),
        sa.CheckConstraint(
            "(reject_reason IS NULL OR char_length(reject_reason) <= 500) "
            "AND (status <> 'Rejected' OR reject_reason IS NOT NULL)",
            name="ck_student_verifications_reject_reason",
        ),
        sa.CheckConstraint(
            "status NOT IN ('Verified', 'Rejected') "
            "OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL)",
            name="ck_student_verifications_reviewed",
        ),
    )
    op.create_index(
        "ix_student_verifications_tutor_id", "student_verifications", ["tutor_id"]
    )
    op.create_index(
        "ix_student_verifications_status_created_at",
        "student_verifications",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_student_verifications_reviewed_by", "student_verifications", ["reviewed_by"]
    )
    op.create_index(
        "ux_student_verifications_evidence_file_ref",
        "student_verifications",
        ["evidence_file_ref"],
        unique=True,
    )
    op.create_index(
        "ux_student_verifications_tutor_id_pending",
        "student_verifications",
        ["tutor_id"],
        unique=True,
        postgresql_where=sa.text("status = 'Pending'"),
    )


def downgrade() -> None:
    op.drop_index("ux_student_verifications_tutor_id_pending", table_name="student_verifications")
    op.drop_index(
        "ux_student_verifications_evidence_file_ref", table_name="student_verifications"
    )
    op.drop_index("ix_student_verifications_reviewed_by", table_name="student_verifications")
    op.drop_index(
        "ix_student_verifications_status_created_at", table_name="student_verifications"
    )
    op.drop_index("ix_student_verifications_tutor_id", table_name="student_verifications")
    op.drop_table("student_verifications")

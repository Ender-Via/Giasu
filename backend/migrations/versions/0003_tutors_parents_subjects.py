"""Hồ sơ vai trò tutors, parents và danh mục subjects (seed môn học).

Revision ID: 0003_tutors_parents_subjects
Revises: 0002_supabase_auth_mapping
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_tutors_parents_subjects"
down_revision: str | None = "0002_supabase_auth_mapping"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SUBJECTS = (
    "Toán",
    "Tiếng Việt",
    "Ngữ văn",
    "Tiếng Anh",
    "Vật lý",
    "Hóa học",
    "Sinh học",
    "Khoa học tự nhiên",
    "Lịch sử",
    "Địa lý",
    "Tin học",
    "Tiếng Trung",
    "Tiếng Nhật",
    "Tiếng Hàn",
    "Tiếng Pháp",
    "IELTS",
    "TOEIC",
    "Luyện chữ đẹp",
    "Vẽ",
    "Piano",
    "Guitar",
    "Lập trình",
)

PHONE_CHECK = "phone ~ '^0[0-9]{9}$'"
REPUTATION_CHECK = "reputation_score IS NULL OR reputation_score BETWEEN 0 AND 100"


def upgrade() -> None:
    op.create_table(
        "tutors",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("phone", sa.Text(), nullable=False),
        sa.Column("verification_status", sa.Text(), server_default="Unverified", nullable=False),
        sa.Column("reputation_score", sa.Numeric(5, 2), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_tutors_users_user_id", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("user_id", name="pk_tutors"),
        sa.CheckConstraint(PHONE_CHECK, name="ck_tutors_phone"),
        sa.CheckConstraint(
            "verification_status IN ('Unverified', 'Pending', 'Verified', 'Rejected')",
            name="ck_tutors_verification_status",
        ),
        sa.CheckConstraint(REPUTATION_CHECK, name="ck_tutors_reputation_score"),
    )

    op.create_table(
        "parents",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("phone", sa.Text(), nullable=False),
        sa.Column("reputation_score", sa.Numeric(5, 2), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_parents_users_user_id", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("user_id", name="pk_parents"),
        sa.CheckConstraint(PHONE_CHECK, name="ck_parents_phone"),
        sa.CheckConstraint(REPUTATION_CHECK, name="ck_parents_reputation_score"),
    )

    subjects = op.create_table(
        "subjects",
        sa.Column("id", sa.SmallInteger(), autoincrement=False, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_subjects"),
        sa.CheckConstraint("char_length(btrim(name)) BETWEEN 1 AND 100", name="ck_subjects_name"),
    )
    op.create_index("ix_subjects_name", "subjects", ["name"], unique=True)
    op.bulk_insert(
        subjects,
        [{"id": index, "name": name} for index, name in enumerate(SUBJECTS, start=1)],
    )


def downgrade() -> None:
    op.drop_index("ix_subjects_name", table_name="subjects")
    op.drop_table("subjects")
    op.drop_table("parents")
    op.drop_table("tutors")

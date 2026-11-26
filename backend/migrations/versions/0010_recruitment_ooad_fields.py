"""Bổ sung mã môn học và tiêu đề tin theo biểu mẫu OOAD."""

import sqlalchemy as sa
from alembic import op

revision = "0010_recruitment_ooad_fields"
down_revision = "0009_recruitment_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "subjects",
        sa.Column(
            "code",
            sa.Text(),
            sa.Computed("'SUB-' || CAST(id AS VARCHAR(6))", persisted=True),
            nullable=False,
        ),
    )
    op.create_index("ix_subjects_code", "subjects", ["code"], unique=True)

    op.add_column("tutor_requests", sa.Column("title", sa.Text(), nullable=True))
    op.create_check_constraint(
        "ck_tutor_requests_title",
        "tutor_requests",
        "title IS NULL OR char_length(btrim(title)) BETWEEN 1 AND 150",
    )


def downgrade() -> None:
    op.drop_constraint("ck_tutor_requests_title", "tutor_requests", type_="check")
    op.drop_column("tutor_requests", "title")
    op.drop_index("ix_subjects_code", table_name="subjects")
    op.drop_column("subjects", "code")

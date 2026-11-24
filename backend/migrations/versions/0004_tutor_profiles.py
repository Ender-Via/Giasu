"""Hồ sơ gia sư, môn của hồ sơ và minh chứng năng lực.

Revision ID: 0004_tutor_profiles
Revises: 0003_tutors_parents_subjects
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_tutor_profiles"
down_revision: str | None = "0003_tutors_parents_subjects"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PROVINCES = (
    "Hà Nội", "TP. Hồ Chí Minh", "Hải Phòng", "Đà Nẵng", "Cần Thơ", "Huế", "An Giang",
    "Bắc Ninh", "Cà Mau", "Cao Bằng", "Đắk Lắk", "Điện Biên", "Đồng Nai", "Đồng Tháp",
    "Gia Lai", "Hà Tĩnh", "Hưng Yên", "Khánh Hòa", "Lai Châu", "Lâm Đồng", "Lạng Sơn",
    "Lào Cai", "Nghệ An", "Ninh Bình", "Phú Thọ", "Quảng Ngãi", "Quảng Ninh", "Quảng Trị",
    "Sơn La", "Tây Ninh", "Thái Nguyên", "Thanh Hóa", "Tuyên Quang", "Vĩnh Long",
)  # fmt: skip


def _in_list(column: str, values: Sequence[str]) -> str:
    quoted = ", ".join("'" + value.replace("'", "''") + "'" for value in values)
    return f"{column} IN ({quoted})"


PROFILE_CHECKS = {
    "ck_tutor_profiles_status": _in_list(
        "status", ("Draft", "PendingReview", "Approved", "Rejected")
    ),
    "ck_tutor_profiles_availability": _in_list("availability", ("Accepting", "Full", "Paused")),
    "ck_tutor_profiles_education_level": _in_list(
        "education_level", ("Primary", "LowerSecondary", "UpperSecondary", "Other")
    ),
    "ck_tutor_profiles_teaching_mode": _in_list("teaching_mode", ("Offline", "Online", "Both")),
    "ck_tutor_profiles_province": _in_list("province", PROVINCES),
    "ck_tutor_profiles_title": "char_length(title) BETWEEN 10 AND 150",
    "ck_tutor_profiles_description": "description IS NULL OR char_length(description) <= 2000",
    "ck_tutor_profiles_fee": (
        "expected_fee_per_session BETWEEN 50000 AND 2000000 AND expected_fee_per_session % 1000 = 0"
    ),
    "ck_tutor_profiles_teaching_wards": (
        "coalesce(cardinality(teaching_wards), 0) <= 5 "
        "AND (teaching_mode = 'Online' OR cardinality(teaching_wards) >= 1)"
    ),
    "ck_tutor_profiles_reject_reason": (
        "(reject_reason IS NULL OR char_length(reject_reason) <= 500) "
        "AND (status <> 'Rejected' OR reject_reason IS NOT NULL)"
    ),
    "ck_tutor_profiles_reviewed": (
        "status NOT IN ('Approved', 'Rejected') "
        "OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL)"
    ),
}


def upgrade() -> None:
    op.create_table(
        "tutor_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tutor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("education_level", sa.Text(), nullable=False),
        sa.Column("teaching_mode", sa.Text(), nullable=False),
        sa.Column("province", sa.Text(), nullable=False),
        sa.Column(
            "teaching_wards",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column("expected_fee_per_session", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), server_default="Draft", nullable=False),
        sa.Column("availability", sa.Text(), server_default="Accepting", nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("reject_reason", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tutor_id"], ["tutors.user_id"], name="fk_tutor_profiles_tutor_id", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"], ["users.id"], name="fk_tutor_profiles_reviewed_by", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tutor_profiles"),
        *(sa.CheckConstraint(sql, name=name) for name, sql in PROFILE_CHECKS.items()),
    )
    op.create_index("ix_tutor_profiles_tutor_id", "tutor_profiles", ["tutor_id"])
    op.create_index("ix_tutor_profiles_reviewed_by", "tutor_profiles", ["reviewed_by"])
    op.create_index(
        "ux_tutor_profiles_tutor_id_default",
        "tutor_profiles",
        ["tutor_id"],
        unique=True,
        postgresql_where=sa.text("is_default"),
    )

    op.create_table(
        "tutor_profile_subjects",
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["tutor_profiles.id"],
            name="fk_tutor_profile_subjects_profile_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"],
            ["subjects.id"],
            name="fk_tutor_profile_subjects_subject_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("profile_id", "subject_id", name="pk_tutor_profile_subjects"),
    )
    op.create_index(
        "ix_tutor_profile_subjects_subject_id", "tutor_profile_subjects", ["subject_id"]
    )

    op.create_table(
        "tutor_profile_evidences",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_ref", sa.Text(), nullable=False),
        sa.Column("file_name", sa.Text(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["tutor_profiles.id"],
            name="fk_tutor_profile_evidences_profile_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tutor_profile_evidences"),
        sa.CheckConstraint(
            _in_list("content_type", ("image/jpeg", "image/png", "application/pdf")),
            name="ck_tutor_profile_evidences_content_type",
        ),
        sa.CheckConstraint(
            "size_bytes BETWEEN 1 AND 5242880", name="ck_tutor_profile_evidences_size_bytes"
        ),
        sa.CheckConstraint(
            "char_length(file_name) BETWEEN 1 AND 255", name="ck_tutor_profile_evidences_file_name"
        ),
    )
    op.create_index(
        "ix_tutor_profile_evidences_profile_id", "tutor_profile_evidences", ["profile_id"]
    )
    op.create_index(
        "ux_tutor_profile_evidences_file_ref", "tutor_profile_evidences", ["file_ref"], unique=True
    )


def downgrade() -> None:
    op.drop_table("tutor_profile_evidences")
    op.drop_table("tutor_profile_subjects")
    op.drop_index("ux_tutor_profiles_tutor_id_default", table_name="tutor_profiles")
    op.drop_index("ix_tutor_profiles_reviewed_by", table_name="tutor_profiles")
    op.drop_index("ix_tutor_profiles_tutor_id", table_name="tutor_profiles")
    op.drop_table("tutor_profiles")

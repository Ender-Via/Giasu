"""Học sinh, tin tìm gia sư và dữ liệu ứng tuyển cần khi đóng tin (FR-05)."""

import sqlalchemy as sa
from alembic import op

revision = "0009_recruitment_requests"
down_revision = "0008_audit_logs"
branch_labels = None
depends_on = None

# Giữ nguyên danh mục D37 tại thời điểm tạo migration.
PROVINCES = (
    "'Hà Nội', 'TP. Hồ Chí Minh', 'Hải Phòng', 'Đà Nẵng', 'Cần Thơ', 'Huế', "
    "'An Giang', 'Bắc Ninh', 'Cà Mau', 'Cao Bằng', 'Đắk Lắk', 'Điện Biên', 'Đồng Nai', "
    "'Đồng Tháp', 'Gia Lai', 'Hà Tĩnh', 'Hưng Yên', 'Khánh Hòa', 'Lai Châu', 'Lâm Đồng', "
    "'Lạng Sơn', 'Lào Cai', 'Nghệ An', 'Ninh Bình', 'Phú Thọ', 'Quảng Ngãi', 'Quảng Ninh', "
    "'Quảng Trị', 'Sơn La', 'Tây Ninh', 'Thái Nguyên', 'Thanh Hóa', 'Tuyên Quang', 'Vĩnh Long'"
)


def upgrade() -> None:
    op.create_table(
        "students",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("parent_id", sa.Uuid(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("grade_level", sa.SmallInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["parents.user_id"], name="fk_students_parent_id", ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("parent_id", "id", name="uq_students_parent_id_id"),
        sa.CheckConstraint(
            "char_length(btrim(full_name)) BETWEEN 2 AND 100", name="ck_students_full_name"
        ),
        sa.CheckConstraint("grade_level BETWEEN 1 AND 12", name="ck_students_grade_level"),
    )
    op.create_index("ix_students_parent_created", "students", ["parent_id", "created_at", "id"])

    op.create_table(
        "tutor_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("parent_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.SmallInteger(), nullable=False),
        sa.Column("education_level", sa.Text(), nullable=False),
        sa.Column("teaching_mode", sa.Text(), nullable=False),
        sa.Column("province", sa.Text(), nullable=True),
        sa.Column("ward", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("sessions_per_week", sa.SmallInteger(), nullable=False),
        sa.Column("min_fee", sa.Integer(), nullable=False),
        sa.Column("max_fee", sa.Integer(), nullable=False),
        sa.Column("requirements", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="PendingReview"),
        sa.Column("reject_reason", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["parents.user_id"],
            name="fk_tutor_requests_parent_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id", "student_id"],
            ["students.parent_id", "students.id"],
            name="fk_tutor_requests_parent_student",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"],
            ["subjects.id"],
            name="fk_tutor_requests_subject_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"], ["users.id"], name="fk_tutor_requests_reviewed_by", ondelete="RESTRICT"
        ),
        sa.CheckConstraint(
            "education_level IN ('Primary', 'LowerSecondary', 'UpperSecondary', 'Other')",
            name="ck_tutor_requests_education_level",
        ),
        sa.CheckConstraint(
            "teaching_mode IN ('Offline', 'Online', 'Both')", name="ck_tutor_requests_teaching_mode"
        ),
        sa.CheckConstraint(
            "(teaching_mode = 'Online' AND province IS NULL AND ward IS NULL AND address IS NULL)"
            " OR (teaching_mode IN ('Offline', 'Both')"
            f" AND province IS NOT NULL AND province IN ({PROVINCES})"
            " AND ward IS NOT NULL AND char_length(btrim(ward)) BETWEEN 1 AND 100"
            " AND (address IS NULL OR char_length(address) <= 200))",
            name="ck_tutor_requests_area",
        ),
        sa.CheckConstraint(
            "sessions_per_week BETWEEN 1 AND 7", name="ck_tutor_requests_sessions_per_week"
        ),
        sa.CheckConstraint(
            "min_fee >= 50000 AND max_fee <= 2000000 AND min_fee <= max_fee",
            name="ck_tutor_requests_fee",
        ),
        sa.CheckConstraint(
            "char_length(btrim(requirements)) BETWEEN 1 AND 2000",
            name="ck_tutor_requests_requirements",
        ),
        sa.CheckConstraint(
            "status IN ('PendingReview', 'Rejected', 'Recruiting', 'Hired', 'Closed')",
            name="ck_tutor_requests_status",
        ),
        sa.CheckConstraint(
            "(reject_reason IS NULL OR char_length(btrim(reject_reason)) BETWEEN 1 AND 500)"
            " AND (status <> 'Rejected' OR reject_reason IS NOT NULL)",
            name="ck_tutor_requests_reject_reason",
        ),
    )
    op.create_index(
        "ix_tutor_requests_parent_updated", "tutor_requests", ["parent_id", "updated_at", "id"]
    )
    op.create_index("ix_tutor_requests_student_id", "tutor_requests", ["student_id"])
    op.create_index("ix_tutor_requests_subject_id", "tutor_requests", ["subject_id"])
    op.create_index(
        "ix_tutor_requests_status_submitted", "tutor_requests", ["status", "submitted_at"]
    )

    op.create_table(
        "tutor_applications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("tutor_id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("introduction", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="Pending"),
        sa.Column("trial_scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["tutor_requests.id"],
            name="fk_tutor_applications_request_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tutor_id"],
            ["tutors.user_id"],
            name="fk_tutor_applications_tutor_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["tutor_profiles.id"],
            name="fk_tutor_applications_profile_id",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "status IN ('Pending', 'Viewed', 'TrialInvited', 'Hired', 'NotHired', 'Rejected',"
            " 'Withdrawn')",
            name="ck_tutor_applications_status",
        ),
    )
    op.create_index(
        "ix_tutor_applications_request_status", "tutor_applications", ["request_id", "status"]
    )
    op.create_index(
        "ix_tutor_applications_tutor_status", "tutor_applications", ["tutor_id", "status"]
    )
    op.create_index(
        "ux_tutor_applications_open",
        "tutor_applications",
        ["request_id", "tutor_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('Pending', 'Viewed', 'TrialInvited')"),
    )


def downgrade() -> None:
    op.drop_table("tutor_applications")
    op.drop_table("tutor_requests")
    op.drop_table("students")

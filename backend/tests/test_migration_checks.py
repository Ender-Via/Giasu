import os
from collections.abc import Generator
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Connection, create_engine, make_url, text
from sqlalchemy.exc import IntegrityError

MIGRATED_URL = os.getenv("MIGRATED_DATABASE_URL", "")


def _migrated_database_name() -> str:
    return (make_url(MIGRATED_URL).database or "") if MIGRATED_URL else ""


pytestmark = pytest.mark.skipif(
    "test" not in _migrated_database_name(),
    reason="Cần MIGRATED_DATABASE_URL trỏ tới database test đã chạy alembic upgrade head",
)

Db = tuple[Connection, UUID, UUID]

INSERT_USER = text(
    "INSERT INTO users (id, role_id, full_name, login_identifier, is_active, token_version, "
    "created_at) VALUES (:id, :role_id, '[TEST] Kiểm CHECK', :email, true, 0, now())"
)
INSERT_PROFILE = text(
    "INSERT INTO tutor_profiles (id, tutor_id, title, description, education_level, teaching_mode, "
    "province, teaching_wards, expected_fee_per_session, status, availability, is_default, "
    "reject_reason, reviewed_by, reviewed_at, created_at, updated_at) VALUES (:id, :tutor_id, "
    ":title, :description, :education_level, :teaching_mode, :province, :teaching_wards, "
    ":expected_fee_per_session, :status, :availability, :is_default, :reject_reason, "
    ":reviewed_by, :reviewed_at, now(), now())"
)
INSERT_REQUEST = text(
    "INSERT INTO tutor_requests (id, parent_id, student_id, subject_id, education_level, "
    "teaching_mode, province, ward, sessions_per_week, min_fee, max_fee, requirements, "
    "title, submitted_at, created_at, updated_at) VALUES ("
    ":id, :parent_id, :student_id, (SELECT min(id) FROM subjects), 'UpperSecondary', "
    ":teaching_mode, :province, :ward, 2, :min_fee, :max_fee, 'Dạy Toán', "
    ":title, now(), now(), now())"
)


@pytest.fixture
def db() -> Generator[Db, None, None]:
    engine = create_engine(MIGRATED_URL)
    with engine.connect() as connection:
        transaction = connection.begin()
        tutor_id, admin_id = uuid4(), uuid4()
        for user_id, role_id in ((tutor_id, 2), (admin_id, 1)):
            connection.execute(
                INSERT_USER,
                {"id": user_id, "role_id": role_id, "email": f"test.check.{user_id}@giasu.local"},
            )
        connection.execute(
            text("INSERT INTO tutors (user_id, phone) VALUES (:id, '0912345678')"),
            {"id": tutor_id},
        )
        yield connection, tutor_id, admin_id
        transaction.rollback()
    engine.dispose()


def profile_params(tutor_id: UUID, **overrides: Any) -> dict[str, Any]:
    params: dict[str, Any] = {
        "id": uuid4(),
        "tutor_id": tutor_id,
        "title": "[TEST] Toán THPT luyện thi",
        "description": "Kiểm CHECK sau migration.",
        "education_level": "UpperSecondary",
        "teaching_mode": "Both",
        "province": "Hà Nội",
        "teaching_wards": ["Phường Hoàn Kiếm"],
        "expected_fee_per_session": 200_000,
        "status": "Draft",
        "availability": "Accepting",
        "is_default": False,
        "reject_reason": None,
        "reviewed_by": None,
        "reviewed_at": None,
    }
    params.update(overrides)
    return params


def violated_constraint(connection: Connection, statement: Any, params: dict[str, Any]) -> str:
    savepoint = connection.begin_nested()
    with pytest.raises(IntegrityError) as caught:
        connection.execute(statement, params)
    savepoint.rollback()
    return caught.value.orig.diag.constraint_name  # type: ignore[union-attr]


def test_request_check_khu_vuc_hoc_phi_va_chu_so_huu(db: Db) -> None:
    connection, _, _ = db
    parent_ids = [uuid4(), uuid4()]
    for parent_id in parent_ids:
        connection.execute(
            INSERT_USER,
            {"id": parent_id, "role_id": 3, "email": f"test.request.{parent_id}@giasu.local"},
        )
        connection.execute(
            text("INSERT INTO parents (user_id, phone) VALUES (:id, '0912345678')"),
            {"id": parent_id},
        )
    student_id = uuid4()
    connection.execute(
        text(
            "INSERT INTO students (id, parent_id, full_name, grade_level, created_at) "
            "VALUES (:id, :parent_id, 'Minh An', 11, now())"
        ),
        {"id": student_id, "parent_id": parent_ids[0]},
    )
    valid = {
        "id": uuid4(),
        "parent_id": parent_ids[0],
        "student_id": student_id,
        "teaching_mode": "Online",
        "province": None,
        "ward": None,
        "min_fee": 150_000,
        "max_fee": 250_000,
        "title": None,
    }
    cases = [
        ({"parent_id": parent_ids[1]}, "fk_tutor_requests_parent_student"),
        ({"province": "Hà Nội"}, "ck_tutor_requests_area"),
        ({"teaching_mode": "Offline", "province": "Hà Nội"}, "ck_tutor_requests_area"),
        ({"max_fee": 100_000}, "ck_tutor_requests_fee"),
        ({"title": " "}, "ck_tutor_requests_title"),
        ({"title": "x" * 151}, "ck_tutor_requests_title"),
    ]
    for changes, constraint in cases:
        assert violated_constraint(connection, INSERT_REQUEST, valid | changes) == constraint
    connection.execute(INSERT_REQUEST, valid)


def test_ma_mon_hoc_sinh_tu_id_va_giu_nguyen_danh_muc_seed(db: Db) -> None:
    connection, _, _ = db
    rows = connection.execute(text("SELECT id, name, code FROM subjects ORDER BY id")).all()
    assert rows[0] == (1, "Toán", "SUB-1")
    assert all(code == f"SUB-{subject_id}" for subject_id, _, code in rows)
    new_code = connection.scalar(
        text("INSERT INTO subjects (id, name) VALUES (1000, 'Môn thử') RETURNING code")
    )
    assert new_code == "SUB-1000"


def test_ho_so_hop_le_luu_duoc(db: Db) -> None:
    connection, tutor_id, admin_id = db
    reviewed = {"reviewed_by": admin_id, "reviewed_at": datetime.now(timezone.utc)}

    connection.execute(INSERT_PROFILE, profile_params(tutor_id, is_default=True))
    connection.execute(INSERT_PROFILE, profile_params(tutor_id, status="Approved", **reviewed))
    connection.execute(
        INSERT_PROFILE, profile_params(tutor_id, teaching_mode="Online", teaching_wards=[])
    )


@pytest.mark.parametrize(
    ("overrides", "constraint"),
    [
        ({"expected_fee_per_session": 150_500}, "ck_tutor_profiles_fee"),
        ({"expected_fee_per_session": 2_001_000}, "ck_tutor_profiles_fee"),
        ({"province": "Quận 1"}, "ck_tutor_profiles_province"),
        ({"title": "Ngắn quá"}, "ck_tutor_profiles_title"),
        ({"status": "Busy"}, "ck_tutor_profiles_status"),
        ({"availability": "Busy"}, "ck_tutor_profiles_availability"),
        ({"teaching_mode": "Offline", "teaching_wards": []}, "ck_tutor_profiles_teaching_wards"),
        ({"teaching_wards": [f"Phường {i}" for i in range(6)]}, "ck_tutor_profiles_teaching_wards"),
        ({"status": "Approved"}, "ck_tutor_profiles_reviewed"),
    ],
    ids=[
        "hoc-phi-le",
        "hoc-phi-qua-tran",
        "tinh-ngoai-danh-muc",
        "tieu-de-ngan",
        "trang-thai-la",
        "nhan-day-la",
        "offline-khong-phuong",
        "qua-5-phuong",
        "duyet-thieu-nguoi-duyet",
    ],
)
def test_check_chan_ho_so_sai(db: Db, overrides: dict[str, Any], constraint: str) -> None:  # BR-04
    connection, tutor_id, _ = db

    assert violated_constraint(
        connection, INSERT_PROFILE, profile_params(tutor_id, **overrides)
    ) == (constraint)


def test_tu_choi_phai_co_ly_do(db: Db) -> None:  # BR-05
    connection, tutor_id, admin_id = db
    params = profile_params(
        tutor_id, status="Rejected", reviewed_by=admin_id, reviewed_at=datetime.now(timezone.utc)
    )

    assert violated_constraint(connection, INSERT_PROFILE, params) == (
        "ck_tutor_profiles_reject_reason"
    )


def test_moi_gia_su_chi_mot_ho_so_mac_dinh(db: Db) -> None:  # BR-02
    connection, tutor_id, _ = db
    connection.execute(INSERT_PROFILE, profile_params(tutor_id, is_default=True))

    assert violated_constraint(
        connection, INSERT_PROFILE, profile_params(tutor_id, is_default=True)
    ) == ("ux_tutor_profiles_tutor_id_default")


def test_minh_chung_qua_5mb_bi_chan(db: Db) -> None:  # BR-03
    connection, tutor_id, _ = db
    profile = profile_params(tutor_id)
    connection.execute(INSERT_PROFILE, profile)
    statement = text(
        "INSERT INTO tutor_profile_evidences (id, profile_id, file_ref, file_name, content_type, "
        "size_bytes, created_at) VALUES (:id, :profile_id, :file_ref, 'a.pdf', "
        "'application/pdf', :size, now())"
    )
    params = {"id": uuid4(), "profile_id": profile["id"], "file_ref": f"test/{uuid4()}.pdf"}

    assert violated_constraint(connection, statement, {**params, "size": 5 * 1024 * 1024 + 1}) == (
        "ck_tutor_profile_evidences_size_bytes"
    )


def test_so_dien_thoai_gia_su_sai_bi_chan(db: Db) -> None:  # BR-01
    connection, _, admin_id = db
    statement = text("INSERT INTO tutors (user_id, phone) VALUES (:id, '123')")

    assert violated_constraint(connection, statement, {"id": admin_id}) == "ck_tutors_phone"


def test_seed_du_22_mon(db: Db) -> None:  # BR-24
    connection, _, _ = db

    names = connection.execute(text("SELECT name FROM subjects ORDER BY id")).scalars().all()

    assert len(names) == 22
    assert names[:4] == ["Toán", "Tiếng Việt", "Ngữ văn", "Tiếng Anh"]

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.core.email_sender import LoggingEmailSender
from app.db.models import (
    AuditLog,
    Notification,
    Parent,
    Student,
    Subject,
    Tutor,
    TutorApplication,
    TutorProfile,
    TutorRequest,
)
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.notifications import NotificationRepository
from app.repositories.recruitment import RecruitmentRepository
from app.repositories.subjects import SubjectRepository
from app.services.errors import ConflictError
from app.services.notifications import NotificationService
from app.services.recruitment import RecruitmentService

pytestmark = pytest.mark.anyio
STUDENTS = "/api/students"
REQUESTS = "/api/tutor-requests"


@pytest.fixture
def add_account(db_session, add_user, make_token):
    def create(role_id: int, *, active: bool = True):
        auth_id = uuid4()
        user = add_user(auth_user_id=auth_id, role_id=role_id, is_active=active)
        if role_id == 2:
            db_session.add(Tutor(user_id=user.id, phone="0912345678"))
        if role_id == 3:
            db_session.add(Parent(user_id=user.id, phone="0912345678"))
        db_session.commit()
        return user, {"Authorization": f"Bearer {make_token(auth_id)}"}

    return create


@pytest.fixture
def parent(add_account):
    return add_account(3)


@pytest.fixture
def subject(db_session):
    item = Subject(id=1, name="Toán")
    db_session.add(item)
    db_session.commit()
    return item


@pytest.fixture
def request_body(db_session, parent, subject):
    user, _ = parent
    student = Student(
        parent_id=user.id, full_name="Nguyễn Minh An", grade_level=11, created_at=utc_now()
    )
    db_session.add(student)
    db_session.commit()
    return {
        "studentId": str(student.id),
        "subjectId": subject.id,
        "educationLevel": "UpperSecondary",
        "teachingMode": "Offline",
        "province": "TP. Hồ Chí Minh",
        "ward": "Phường Bến Thành",
        "address": "10 Đường A",
        "sessionsPerWeek": 2,
        "minFee": 150_000,
        "maxFee": 250_000,
        "requirements": "  Dạy tối thứ 3 và thứ 6.  ",
    }


async def create_request(client, parent, request_body):
    response = await client.post(REQUESTS, headers=parent[1], json=request_body)
    assert response.status_code == 201, response.text
    return response.json()["data"]


async def test_ac_request_01_them_sua_va_sap_xep_hoc_sinh(client: AsyncClient, parent):
    headers = parent[1]
    created = await client.post(
        STUDENTS, headers=headers, json={"fullName": "  Nguyễn Minh An  ", "gradeLevel": 9}
    )
    assert created.status_code == 201
    first = created.json()["data"]
    assert first["fullName"] == "Nguyễn Minh An"
    edited = await client.put(
        f"{STUDENTS}/{first['id']}",
        headers=headers,
        json={"fullName": "Nguyễn Minh An", "gradeLevel": 10},
    )
    second = await client.post(
        STUDENTS, headers=headers, json={"fullName": "Trần Minh An", "gradeLevel": 12}
    )
    assert edited.status_code == 200
    result = await client.get(f"{STUDENTS}/mine", headers=headers)
    assert [(x["id"], x["gradeLevel"]) for x in result.json()["data"]] == [
        (first["id"], 10),
        (second.json()["data"]["id"], 12),
    ]


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"fullName": " A ", "gradeLevel": 1}, "Họ tên"),
        ({"fullName": "Minh", "gradeLevel": 0}, "Lớp"),
        ({"fullName": "Minh", "gradeLevel": 13}, "Lớp"),
        ({"fullName": "Minh", "gradeLevel": True}, "Lớp"),
        ({"fullName": "Minh"}, "gradeLevel"),
    ],
)
async def test_ac_request_02_hoc_sinh_sai_truong(client, parent, body, field):
    response = await client.post(STUDENTS, headers=parent[1], json=body)
    assert response.status_code == 400
    assert any(field in error for error in response.json()["errors"])
    mine = await client.get(f"{STUDENTS}/mine", headers=parent[1])
    assert mine.json()["data"] == []


async def test_ac_request_03_pham_vi_hoc_sinh(client, add_account, request_body):
    other = add_account(3)[1]
    tutor = add_account(2)[1]
    student_id = request_body["studentId"]
    payload = {"fullName": "Minh An", "gradeLevel": 1}
    results = [
        await client.put(f"{STUDENTS}/{student_id}", headers=other, json=payload),
        await client.post(REQUESTS, headers=other, json=request_body),
        await client.post(STUDENTS, headers=tutor, json=payload),
    ]
    assert [result.status_code for result in results] == [404, 404, 403]
    assert (
        results[0].json()["message"] == results[1].json()["message"] == "Không tìm thấy học sinh."
    )


async def test_ac_request_04_dang_tin_ghi_nhat_ky_va_bao_admin(
    client, parent, request_body, add_account, db_session: Session
):
    admins = [add_account(1)[0], add_account(1)[0]]
    add_account(1, active=False)
    tutor = add_account(2)[1]
    request_body.update(status="Recruiting", expiresAt="2026-12-25", parentId=str(uuid4()))
    item = await create_request(client, parent, request_body)
    assert item["status"] == "PendingReview"
    assert item["expiresAtUtc"] is None
    assert item["title"] is None
    assert item["requirements"] == "Dạy tối thứ 3 và thứ 6."
    assert (await client.get(f"{REQUESTS}/{item['id']}", headers=tutor)).status_code == 404

    logs = list(db_session.scalars(select(AuditLog)))
    assert [(log.actor_id, log.from_status, log.to_status) for log in logs] == [
        (parent[0].id, None, "PendingReview")
    ]
    notices = list(db_session.scalars(select(Notification)))
    assert {(notice.recipient_id, notice.type) for notice in notices} == {
        (admin.id, "ModerationQueue") for admin in admins
    }


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"minFee": 300_000}, "lớn hơn"),
        ({"minFee": 40_000}, "tối thiểu"),
        ({"sessionsPerWeek": 8}, "Số buổi"),
        ({"ward": None}, "Phường"),
        ({"province": "Quận 1"}, "tỉnh/thành"),
        ({"subjectId": 323}, "môn"),
        ({"requirements": "a" * 2001}, "Yêu cầu"),
        ({"address": "a" * 201}, "Địa chỉ"),
        ({"title": "a" * 151}, "Tiêu đề"),
        ({"title": 123}, "Tiêu đề"),
    ],
)
async def test_ac_request_05_tin_sai_truong(client, parent, request_body, change, field):
    response = await client.post(REQUESTS, headers=parent[1], json={**request_body, **change})
    assert response.status_code == 400, response.text
    assert any(field in error for error in response.json()["errors"])
    mine = await client.get(f"{REQUESTS}/mine", headers=parent[1])
    assert mine.json()["data"]["totalCount"] == 0


async def test_ac_request_06_online_bo_qua_khu_vuc(client, parent, request_body):
    request_body["teachingMode"] = "Online"
    no_area = {k: v for k, v in request_body.items() if k not in {"province", "ward", "address"}}
    for body in (no_area, {**request_body, "province": 15, "address": {"ignored": True}}):
        created = await create_request(client, parent, body)
        assert [created[key] for key in ("province", "ward", "address")] == [None, None, None]


async def test_tieu_de_tin_tuy_chon_va_tuong_thich_client_cu(client, parent, request_body):
    title = "Tìm gia sư Toán lớp 11"
    item = await create_request(client, parent, {**request_body, "title": f" {title} "})
    assert item["title"] == title
    detail_path = f"{REQUESTS}/{item['id']}"

    response = await client.put(detail_path, headers=parent[1], json=request_body)
    assert response.status_code == 200
    assert response.json()["data"]["title"] == title
    listing = await client.get(f"{REQUESTS}/mine", headers=parent[1])
    assert listing.json()["data"]["items"][0]["title"] == title

    response = await client.put(
        detail_path, headers=parent[1], json={**request_body, "title": None}
    )
    assert response.status_code == 200
    assert response.json()["data"]["title"] is None


def set_request_status(db_session, item, status):
    request = db_session.get(TutorRequest, UUID(item["id"]))
    request.status = status
    if status == "Recruiting":
        request.expires_at = utc_now()
        request.reviewed_at = utc_now()
    if status == "Rejected":
        request.reject_reason = "Cần chỉnh yêu cầu."
    db_session.commit()
    return request


def add_application(db_session, add_account, request, status):
    user, headers = add_account(2)
    now = utc_now()
    profile = TutorProfile(
        tutor_id=user.id,
        title="Hồ sơ Toán luyện thi",
        education_level="UpperSecondary",
        teaching_mode="Online",
        province="Hà Nội",
        expected_fee_per_session=150_000,
        created_at=now,
        updated_at=now,
    )
    db_session.add(profile)
    db_session.flush()
    application = TutorApplication(
        request_id=request.id,
        tutor_id=user.id,
        profile_id=profile.id,
        introduction="Tôi có kinh nghiệm dạy luyện thi.",
        status=status,
        created_at=now,
        updated_at=now,
    )
    db_session.add(application)
    db_session.commit()
    return application, headers


async def test_ac_request_07_sua_tin_da_duyet_giu_phieu_va_gui_lai(
    client, parent, request_body, add_account, db_session
):
    admin, admin_headers = add_account(1)
    created = await create_request(client, parent, request_body)
    request = set_request_status(db_session, created, "Recruiting")
    applications = [add_application(db_session, add_account, request, "Pending") for _ in range(2)]
    path = f"{REQUESTS}/{request.id}"

    public = (await client.get(path, headers=applications[0][1])).json()["data"]
    assert public["hasOpenApplication"] is True
    assert {"address", "studentId", "studentName", "parent"}.isdisjoint(public)
    admin_item = (await client.get(path, headers=admin_headers)).json()["data"]
    assert admin_item["address"] == request_body["address"]
    assert admin_item["parent"]["email"] == parent[0].login_identifier

    edited = await client.put(path, headers=parent[1], json={**request_body, "maxFee": 275_000})
    assert edited.status_code == 200, edited.text
    item = edited.json()["data"]
    assert (item["status"], item["openApplicationCount"], item["expiresAtUtc"]) == (
        "PendingReview",
        2,
        None,
    )
    assert all(application.status == "Pending" for application, _ in applications)
    assert (await client.get(path, headers=applications[0][1])).status_code == 404
    notices = list(
        db_session.scalars(select(Notification).where(Notification.recipient_id == admin.id))
    )
    assert len(notices) == 2


async def test_sua_tin_cho_duyet_va_gui_lai_tin_tu_choi(
    client, parent, request_body, add_account, db_session
):
    add_account(1)
    item = await create_request(client, parent, request_body)
    path = f"{REQUESTS}/{item['id']}"
    result = await client.put(path, headers=parent[1], json=request_body)
    assert result.json()["data"]["submittedAtUtc"] == item["submittedAtUtc"]
    assert len(list(db_session.scalars(select(Notification)))) == 1
    set_request_status(db_session, item, "Rejected")
    result = await client.put(path, headers=parent[1], json=request_body)
    assert result.json()["data"]["rejectReason"] == "Cần chỉnh yêu cầu."
    assert result.json()["data"]["status"] == "PendingReview"
    assert len(list(db_session.scalars(select(Notification)))) == 2


@pytest.mark.parametrize("status", ["Hired", "Closed"])
async def test_ac_request_08_khong_sua_tin_ket_thuc(
    client, parent, request_body, db_session, status
):
    item = await create_request(client, parent, request_body)
    request = set_request_status(db_session, item, status)
    result = await client.put(
        f"{REQUESTS}/{request.id}", headers=parent[1], json={**request_body, "minFee": 190_000}
    )
    assert result.status_code == 409
    assert request.min_fee == 150_000


async def test_ac_request_09_dong_tin_cap_nhat_phieu_thong_bao_va_audit(
    client, parent, request_body, add_account, db_session
):
    item = await create_request(client, parent, request_body)
    path = f"{REQUESTS}/{item['id']}/close"
    assert (await client.post(path, headers=parent[1])).status_code == 409
    request = set_request_status(db_session, item, "Recruiting")
    initial = ["Pending", "Viewed", "TrialInvited", "Withdrawn"]
    applications = [add_application(db_session, add_account, request, s)[0] for s in initial]
    listed = await client.get(f"{REQUESTS}/mine", headers=parent[1])
    assert listed.json()["data"]["items"][0]["openApplicationCount"] == 3

    response = await client.post(path, headers=parent[1])
    assert response.status_code == 200, response.text
    assert response.json()["data"]["status"] == "Closed"
    assert response.json()["data"]["openApplicationCount"] == 0
    assert (await client.post(path, headers=parent[1])).status_code == 409
    expected = ["Rejected", "Rejected", "NotHired", "Withdrawn"]
    assert [app.status for app in applications] == expected

    notices = list(db_session.scalars(select(Notification)))
    assert {notice.recipient_id for notice in notices} == {app.tutor_id for app in applications[:3]}
    assert len(notices) == 3 and all(notice.type == "ApplicationStatus" for notice in notices)
    logs = list(db_session.scalars(select(AuditLog)))
    assert {(log.entity_id, log.from_status, log.to_status) for log in logs} == {
        (request.id, None, "PendingReview"),
        (request.id, "Recruiting", "Closed"),
        *(
            (app.id, before, after)
            for app, before, after in zip(applications[:3], initial[:3], expected[:3], strict=True)
        ),
    }


async def test_ac_request_10_ngoai_pham_vi_va_phan_trang(client, parent, request_body, add_account):
    first = await create_request(client, parent, request_body)
    second = await create_request(client, parent, request_body)
    other = add_account(3)[1]
    admin = add_account(1)[1]
    path = f"{REQUESTS}/{first['id']}"
    results = [
        await client.get(path, headers=other),
        await client.put(path, headers=other, json=request_body),
        await client.post(f"{path}/close", headers=other),
    ]
    assert all(
        r.status_code == 404 and r.json()["message"] == "Không tìm thấy tin." for r in results
    )
    assert (await client.post(f"{path}/close", headers=admin)).status_code == 403
    assert (await client.get(f"{REQUESTS}/mine", headers=other)).json()["data"]["items"] == []
    page = await client.get(
        f"{REQUESTS}/mine",
        headers=parent[1],
        params={"pageSize": 1, "status": "PendingReview", "studentId": request_body["studentId"]},
    )
    data = page.json()["data"]
    assert (data["totalCount"], data["pageSize"], data["items"][0]["id"]) == (2, 1, second["id"])
    assert (await client.get(f"{REQUESTS}/mine?pageSize=101", headers=parent[1])).status_code == 400


async def test_dong_tin_rollback_khi_khong_ghi_duoc_thong_bao(
    client, parent, request_body, add_account, db_session, monkeypatch
):
    item = await create_request(client, parent, request_body)
    request = set_request_status(db_session, item, "Recruiting")
    application, _ = add_application(db_session, add_account, request, "TrialInvited")

    def queue_failed(*args, **kwargs):
        raise RuntimeError("Không ghi được thông báo.")

    monkeypatch.setattr(NotificationService, "queue_many", queue_failed)
    result = await client.post(f"{REQUESTS}/{request.id}/close", headers=parent[1])
    assert result.status_code == 500
    assert request.status == "Recruiting"
    assert application.status == "TrialInvited"
    assert list(db_session.scalars(select(Notification))) == []
    assert [log.to_status for log in db_session.scalars(select(AuditLog))] == ["PendingReview"]


async def test_dong_tin_dong_thoi_chi_thanh_cong_mot_lan(
    client, parent, request_body, add_account, db_session
):
    if db_session.bind.dialect.name != "postgresql":
        pytest.skip("Cần PostgreSQL để kiểm khóa dòng.")

    item = await create_request(client, parent, request_body)
    request = set_request_status(db_session, item, "Recruiting")
    add_application(db_session, add_account, request, "Viewed")
    request_id, parent_id = request.id, parent[0].id
    barrier = Barrier(2, timeout=5)

    def close():
        with Session(db_session.bind, autoflush=False, expire_on_commit=False) as session:
            service = RecruitmentService(
                RecruitmentRepository(session),
                SubjectRepository(session),
                AuditLogRepository(session),
                NotificationService(NotificationRepository(session), LoggingEmailSender()),
            )
            barrier.wait()
            try:
                service.close_request(parent_id, request_id)
            except ConflictError:
                return 409
            return 200

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [pool.submit(close) for _ in range(2)]
        assert sorted(future.result(timeout=10) for future in results) == [200, 409]
    assert len(list(db_session.scalars(select(Notification)))) == 1

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import NotificationType, TutorProfileStatus
from app.core.email_sender import LoggingEmailSender
from app.core.recruitment_status import TutorRequestStatus
from app.db.models import (
    AuditLog,
    Notification,
    Student,
    TutorProfile,
    TutorRequest,
)
from app.repositories.admin_review import AdminReviewRepository
from app.repositories.audit_logs import AuditLogRepository
from app.repositories.notifications import NotificationRepository
from app.services.admin_review import AdminReviewService
from app.services.errors import ConflictError
from app.services.notifications import NotificationService
from tests.fakes import JPEG_BYTES, PDF_BYTES, InMemoryFileStorage

pytestmark = pytest.mark.anyio


@pytest.fixture
def make_parent_and_student(db_session: Session, make_account):  # type: ignore[no-untyped-def]
    def create():
        parent_account = make_account(3)
        student = Student(
            id=uuid4(),
            parent_id=parent_account.user_id,
            full_name="Nguyễn Minh An",
            grade_level=11,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(student)
        db_session.commit()
        return parent_account, student

    return create


async def _create_pending_profile(
    client: AsyncClient, tutor, create_profile, db_session: Session, *, title: str | None = None
) -> dict:
    payload = {"title": title} if title else {}
    profile = await create_profile(tutor, **payload)
    for name, data, content_type in (
        ("bang-diem.pdf", PDF_BYTES, "application/pdf"),
        ("chung-chi.jpg", JPEG_BYTES, "image/jpeg"),
    ):
        uploaded = await client.post(
            f"/api/tutor-profiles/{profile['id']}/evidences",
            files={"files": (name, data, content_type)},
            headers=tutor.headers,
        )
        assert uploaded.status_code == 201
    submitted = await client.post(
        f"/api/tutor-profiles/{profile['id']}/submit", headers=tutor.headers
    )
    assert submitted.status_code == 200
    return submitted.json()["data"]


async def _create_pending_request(
    client: AsyncClient, parent_account, student_id: UUID, subject_id: int
) -> dict:
    response = await client.post(
        "/api/tutor-requests",
        headers=parent_account.headers,
        json={
            "studentId": str(student_id),
            "subjectId": subject_id,
            "title": "[TEST] Cần gia sư Toán lớp 11",
            "educationLevel": "UpperSecondary",
            "teachingMode": "Offline",
            "province": "TP. Hồ Chí Minh",
            "ward": "Phường Bến Thành",
            "address": "12 Lê Lợi",
            "sessionsPerWeek": 2,
            "minFee": 150_000,
            "maxFee": 250_000,
            "requirements": "Sinh viên năm 3 trở lên, dạy tối thứ 3 và thứ 6.",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


async def test_danh_sach_ho_so_cho_duyet_sap_xep_va_chan_draft(  # AC-ADMIN-REVIEW-01
    client: AsyncClient, db_session: Session, make_account, tutor, other_tutor, create_profile
) -> None:
    admin = make_account(1)
    h1 = await _create_pending_profile(
        client, tutor, create_profile, db_session, title="[TEST] Hồ sơ H1 gửi trước"
    )
    h2 = await _create_pending_profile(
        client, other_tutor, create_profile, db_session, title="[TEST] Hồ sơ H2 gửi sau"
    )
    h3_draft = await create_profile(tutor, title="[TEST] Hồ sơ H3 đang nháp")
    h4_approved = await create_profile(other_tutor, title="[TEST] Hồ sơ H4 đã duyệt")

    t1 = datetime(2026, 11, 23, 8, 0, tzinfo=timezone.utc)
    row1 = db_session.get(TutorProfile, UUID(h1["id"]))
    row2 = db_session.get(TutorProfile, UUID(h2["id"]))
    row4 = db_session.get(TutorProfile, UUID(h4_approved["id"]))
    assert row1 is not None and row2 is not None and row4 is not None
    row1.submitted_at = t1
    row2.submitted_at = t1 + timedelta(hours=1)
    row4.status = TutorProfileStatus.APPROVED
    row4.reviewed_by = admin.user_id
    row4.reviewed_at = t1 + timedelta(hours=2)
    db_session.commit()

    pending = await client.get("/api/tutor-profiles", headers=admin.headers)
    assert pending.status_code == 200
    data = pending.json()["data"]
    assert data["totalCount"] == 2
    assert [item["id"] for item in data["items"]] == [h1["id"], h2["id"]]
    assert all(item["id"] not in {h3_draft["id"], h4_approved["id"]} for item in data["items"])
    assert data["items"][0]["tutor"]["verificationStatus"] == "Unverified"

    draft_filter = await client.get("/api/tutor-profiles?status=Draft", headers=admin.headers)
    assert draft_filter.status_code == 400

    approved_list = await client.get("/api/tutor-profiles?status=Approved", headers=admin.headers)
    assert approved_list.status_code == 200
    assert [item["id"] for item in approved_list.json()["data"]["items"]] == [h4_approved["id"]]
    assert approved_list.json()["data"]["items"][0]["reviewedByName"] is not None


async def test_admin_xem_chi_tiet_va_duyet_ho_so(  # AC-ADMIN-REVIEW-02, BR-22
    client: AsyncClient, db_session: Session, make_account, tutor, create_profile
) -> None:
    admin = make_account(1)
    profile = await create_profile(tutor, title="[TEST] Toán THPT luyện thi đại học")
    for name, data, content_type in (
        ("bang-diem.pdf", PDF_BYTES, "application/pdf"),
        ("chung-chi.jpg", JPEG_BYTES, "image/jpeg"),
    ):
        await client.post(
            f"/api/tutor-profiles/{profile['id']}/evidences",
            files={"files": (name, data, content_type)},
            headers=tutor.headers,
        )

    row = db_session.get(TutorProfile, UUID(profile["id"]))
    assert row is not None
    row.status = TutorProfileStatus.PENDING_REVIEW
    row.submitted_at = datetime.now(timezone.utc)
    row.reject_reason = "Thiếu bảng điểm."
    db_session.commit()

    detail = await client.get(f"/api/tutor-profiles/{profile['id']}", headers=admin.headers)
    assert detail.status_code == 200
    detail_data = detail.json()["data"]
    assert detail_data["rejectReason"] == "Thiếu bảng điểm."
    assert detail_data["tutor"]["verificationStatus"] == "Unverified"
    assert detail_data["tutor"]["phone"] == "0912345678"
    assert len(detail_data["evidences"]) == 2
    assert all(ev["url"].endswith("expiresIn=3600") for ev in detail_data["evidences"])

    approved = await client.post(
        f"/api/tutor-profiles/{profile['id']}/approve", headers=admin.headers
    )
    assert approved.status_code == 200
    approved_data = approved.json()["data"]
    assert approved_data["status"] == TutorProfileStatus.APPROVED
    assert approved_data["rejectReason"] is None
    assert approved_data["reviewedAtUtc"] is not None
    assert approved_data["reviewedByName"] is not None

    notis = await client.get("/api/notifications", headers=tutor.headers)
    assert notis.json()["data"]["totalCount"] == 1
    assert notis.json()["data"]["items"][0]["type"] == NotificationType.MODERATION_RESULT

    logs = list(
        db_session.scalars(
            select(AuditLog).where(
                AuditLog.entity == "TutorProfile",
                AuditLog.entity_id == UUID(profile["id"]),
            )
        )
    )
    assert any(
        log.actor_id == admin.user_id
        and log.from_status == TutorProfileStatus.PENDING_REVIEW
        and log.to_status == TutorProfileStatus.APPROVED
        for log in logs
    )


async def test_admin_tu_choi_ho_so_bat_buoc_ly_do_va_gui_lai_duoc(  # AC-ADMIN-REVIEW-03, BR-05
    client: AsyncClient, db_session: Session, make_account, tutor, create_profile
) -> None:
    admin = make_account(1)
    profile = await _create_pending_profile(client, tutor, create_profile, db_session)

    missing_body = await client.post(
        f"/api/tutor-profiles/{profile['id']}/reject", json={}, headers=admin.headers
    )
    blank_reason = await client.post(
        f"/api/tutor-profiles/{profile['id']}/reject",
        json={"reason": "   "},
        headers=admin.headers,
    )
    too_long = await client.post(
        f"/api/tutor-profiles/{profile['id']}/reject",
        json={"reason": "a" * 501},
        headers=admin.headers,
    )
    assert (missing_body.status_code, blank_reason.status_code, too_long.status_code) == (
        400,
        400,
        400,
    )

    still_pending = await client.get(f"/api/tutor-profiles/{profile['id']}", headers=tutor.headers)
    assert still_pending.json()["data"]["status"] == TutorProfileStatus.PENDING_REVIEW

    rejected = await client.post(
        f"/api/tutor-profiles/{profile['id']}/reject",
        json={"reason": "  Minh chứng IELTS mờ.  "},
        headers=admin.headers,
    )
    assert rejected.status_code == 200
    assert rejected.json()["data"]["status"] == TutorProfileStatus.REJECTED
    assert rejected.json()["data"]["rejectReason"] == "Minh chứng IELTS mờ."

    notis = await client.get("/api/notifications", headers=tutor.headers)
    assert notis.json()["data"]["items"][0]["type"] == NotificationType.MODERATION_RESULT

    resubmitted = await client.post(
        f"/api/tutor-profiles/{profile['id']}/submit", headers=tutor.headers
    )
    assert resubmitted.status_code == 200
    assert resubmitted.json()["data"]["status"] == TutorProfileStatus.PENDING_REVIEW


async def test_khong_duyet_ho_so_sai_trang_thai_va_khong_ton_tai(  # AC-ADMIN-REVIEW-04
    client: AsyncClient, db_session: Session, make_account, tutor, create_profile
) -> None:
    admin = make_account(1)
    profile = await _create_pending_profile(client, tutor, create_profile, db_session)
    approved = await client.post(
        f"/api/tutor-profiles/{profile['id']}/approve", headers=admin.headers
    )
    assert approved.status_code == 200

    approve_again = await client.post(
        f"/api/tutor-profiles/{profile['id']}/approve", headers=admin.headers
    )
    reject_approved = await client.post(
        f"/api/tutor-profiles/{profile['id']}/reject",
        json={"reason": "Không duyệt"},
        headers=admin.headers,
    )
    not_found = await client.post(
        f"/api/tutor-profiles/{uuid4()}/approve", headers=admin.headers
    )
    assert (approve_again.status_code, reject_approved.status_code, not_found.status_code) == (
        409,
        409,
        404,
    )


async def test_duyet_va_tu_choi_ho_so_dong_thoi_chi_mot_nguoi_thanh_cong(  # AC-ADMIN-REVIEW-04
    client: AsyncClient, db_session: Session, make_account, tutor, create_profile
) -> None:
    if db_session.bind.dialect.name != "postgresql":
        pytest.skip("Cần PostgreSQL để kiểm tra cập nhật đồng thời.")

    admin_1 = make_account(1)
    admin_2 = make_account(1)
    profile = await _create_pending_profile(client, tutor, create_profile, db_session)
    profile_id = UUID(profile["id"])
    barrier = Barrier(2, timeout=5)

    def worker(approve: bool) -> int:
        with Session(db_session.bind, autoflush=False, expire_on_commit=False) as session:
            service = AdminReviewService(
                AdminReviewRepository(session),
                InMemoryFileStorage(),
                NotificationService(NotificationRepository(session), LoggingEmailSender()),
                AuditLogRepository(session),
            )
            barrier.wait()
            try:
                if approve:
                    service.approve_tutor_profile(admin_1.user_id, profile_id)
                else:
                    service.reject_tutor_profile(admin_2.user_id, profile_id, "Từ chối")
            except ConflictError:
                return 409
            return 200

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [pool.submit(worker, True), pool.submit(worker, False)]
        assert sorted(future.result(timeout=10) for future in results) == [200, 409]

    audit_rows = list(
        db_session.scalars(
            select(AuditLog).where(
                AuditLog.entity == "TutorProfile",
                AuditLog.entity_id == profile_id,
                AuditLog.from_status == TutorProfileStatus.PENDING_REVIEW,
            )
        )
    )
    assert len(audit_rows) == 1


async def test_admin_danh_sach_va_duyet_tin_tim_gia_su(  # AC-ADMIN-REVIEW-05, D33
    client: AsyncClient,
    db_session: Session,
    make_account,
    make_parent_and_student,
    subjects,
    monkeypatch,
) -> None:
    admin = make_account(1)
    parent_account, student = make_parent_and_student()
    subject = subjects[0]
    t1 = await _create_pending_request(client, parent_account, student.id, subject.id)
    t2 = await _create_pending_request(client, parent_account, student.id, subject.id)

    row1 = db_session.get(TutorRequest, UUID(t1["id"]))
    row2 = db_session.get(TutorRequest, UUID(t2["id"]))
    assert row1 is not None and row2 is not None
    row1.submitted_at = datetime(2026, 11, 23, 2, 0, tzinfo=timezone.utc)
    row2.submitted_at = datetime(2026, 11, 23, 2, 30, tzinfo=timezone.utc)
    db_session.commit()

    listed = await client.get("/api/tutor-requests", headers=admin.headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["data"]["items"]] == [t1["id"], t2["id"]]

    invalid_status = await client.get("/api/tutor-requests?status=Unknown", headers=admin.headers)
    assert invalid_status.status_code == 400

    detail = await client.get(f"/api/tutor-requests/{t1['id']}", headers=admin.headers)
    assert detail.status_code == 200
    detail_data = detail.json()["data"]
    assert detail_data["address"] == "12 Lê Lợi"
    assert detail_data["studentName"] == "Nguyễn Minh An"
    assert detail_data["studentGradeLevel"] == 11
    assert detail_data["parent"]["phone"] == "0987654321"

    # 10:00 ngày 23/11/2026 giờ Việt Nam (UTC+7) = 03:00 UTC
    approve_time_utc = datetime(2026, 11, 23, 3, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("app.services.admin_review.utc_now", lambda: approve_time_utc)

    approved = await client.post(f"/api/tutor-requests/{t1['id']}/approve", headers=admin.headers)
    assert approved.status_code == 200
    approved_data = approved.json()["data"]
    assert approved_data["status"] == TutorRequestStatus.RECRUITING
    assert approved_data["expiresAtUtc"] == "2026-12-23T03:00:00Z"
    assert approved_data["reviewedByName"] is not None

    parent_notis = list(
        db_session.scalars(
            select(Notification).where(Notification.recipient_id == parent_account.user_id)
        )
    )
    assert len(parent_notis) == 1
    assert parent_notis[0].type == NotificationType.MODERATION_RESULT

    logs = list(
        db_session.scalars(
            select(AuditLog).where(
                AuditLog.entity == "TutorRequest",
                AuditLog.entity_id == UUID(t1["id"]),
            )
        )
    )
    assert any(
        log.actor_id == admin.user_id
        and log.from_status == TutorRequestStatus.PENDING_REVIEW
        and log.to_status == TutorRequestStatus.RECRUITING
        for log in logs
    )


async def test_admin_tu_choi_tin_va_xung_dot_trang_thai(  # AC-ADMIN-REVIEW-06, BR-05, BR-06
    client: AsyncClient, db_session: Session, make_account, make_parent_and_student, subjects
) -> None:
    admin = make_account(1)
    parent_account, student = make_parent_and_student()
    req = await _create_pending_request(client, parent_account, student.id, subjects[0].id)

    empty = await client.post(
        f"/api/tutor-requests/{req['id']}/reject", json={"reason": "  "}, headers=admin.headers
    )
    too_long = await client.post(
        f"/api/tutor-requests/{req['id']}/reject",
        json={"reason": "x" * 501},
        headers=admin.headers,
    )
    assert (empty.status_code, too_long.status_code) == (400, 400)

    rejected = await client.post(
        f"/api/tutor-requests/{req['id']}/reject",
        json={"reason": "Tin yêu cầu phí nhận lớp, vi phạm quy chế."},
        headers=admin.headers,
    )
    assert rejected.status_code == 200
    assert rejected.json()["data"]["status"] == TutorRequestStatus.REJECTED
    assert rejected.json()["data"]["rejectReason"] == "Tin yêu cầu phí nhận lớp, vi phạm quy chế."
    assert rejected.json()["data"]["expiresAtUtc"] is None

    approve_rejected = await client.post(
        f"/api/tutor-requests/{req['id']}/approve", headers=admin.headers
    )
    not_found = await client.post(
        f"/api/tutor-requests/{uuid4()}/reject",
        json={"reason": "Không tồn tại"},
        headers=admin.headers,
    )
    assert (approve_rejected.status_code, not_found.status_code) == (409, 404)


async def test_chi_admin_duyet_va_admin_khong_sua_dong(  # AC-ADMIN-REVIEW-07, BR-SCOPE-04
    client: AsyncClient,
    db_session: Session,
    make_account,
    tutor,
    create_profile,
    make_parent_and_student,
    subjects,
) -> None:
    admin = make_account(1)
    parent_account, student = make_parent_and_student()
    subject = subjects[0]
    profile = await _create_pending_profile(client, tutor, create_profile, db_session)
    req = await _create_pending_request(client, parent_account, student.id, subject.id)

    calls = [
        await client.post(f"/api/tutor-profiles/{profile['id']}/approve", headers=tutor.headers),
        await client.get("/api/tutor-profiles?status=PendingReview", headers=tutor.headers),
        await client.post(
            f"/api/tutor-requests/{req['id']}/approve", headers=parent_account.headers
        ),
        await client.put(
            f"/api/tutor-requests/{req['id']}",
            headers=admin.headers,
            json={
                "studentId": str(student.id),
                "subjectId": subject.id,
                "educationLevel": "UpperSecondary",
                "teachingMode": "Online",
                "sessionsPerWeek": 2,
                "minFee": 150_000,
                "maxFee": 250_000,
                "requirements": "Sửa lậu",
            },
        ),
        await client.post(f"/api/tutor-requests/{req['id']}/close", headers=admin.headers),
        await client.get(f"/api/tutor-profiles/{profile['id']}", headers=parent_account.headers),
    ]
    assert all(res.status_code == 403 for res in calls)

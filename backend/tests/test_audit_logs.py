from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import VerificationStatus
from app.db.models import AuditLog
from app.repositories.audit_logs import AuditLogRepository
from app.services.audit_logs import AuditLogService
from tests.fakes import JPEG_BYTES

pytestmark = pytest.mark.anyio


async def test_audit_log_luu_chuyen_trang_thai_xac_thuc_sinh_vien(  # AC-VERIFY-04, BR-22, NFR-04
    client: AsyncClient, db_session: Session, make_account, tutor
) -> None:
    admin = make_account(1)
    submitted = await client.post(
        "/api/student-verifications",
        data={"university": "ĐH Bách Khoa", "studentCode": "22520001"},
        files={"file": ("the.jpg", JPEG_BYTES, "image/jpeg")},
        headers=tutor.headers,
    )
    assert submitted.status_code == 201
    verification_id = UUID(submitted.json()["data"]["id"])

    rejected = await client.post(
        f"/api/student-verifications/{verification_id}/reject",
        json={"reason": "Ảnh thẻ mờ."},
        headers=admin.headers,
    )
    assert rejected.status_code == 200

    resubmitted = await client.post(
        "/api/student-verifications",
        data={"university": "ĐH Bách Khoa", "studentCode": "22520002"},
        files={"file": ("the.jpg", JPEG_BYTES, "image/jpeg")},
        headers=tutor.headers,
    )
    assert resubmitted.status_code == 201
    second_id = UUID(resubmitted.json()["data"]["id"])

    approved = await client.post(
        f"/api/student-verifications/{second_id}/approve", headers=admin.headers
    )
    assert approved.status_code == 200

    audit_service = AuditLogService(AuditLogRepository(db_session))
    first_logs = audit_service.list_for_entity("StudentVerification", verification_id)
    second_logs = audit_service.list_for_entity("StudentVerification", second_id)

    assert [(log.actor_id, log.action, log.from_status, log.to_status) for log in first_logs] == [
        (tutor.user_id, "Submit", None, VerificationStatus.PENDING),
        (admin.user_id, "Reject", VerificationStatus.PENDING, VerificationStatus.REJECTED),
    ]
    assert [(log.actor_id, log.action, log.from_status, log.to_status) for log in second_logs] == [
        (tutor.user_id, "Submit", None, VerificationStatus.PENDING),
        (admin.user_id, "Approve", VerificationStatus.PENDING, VerificationStatus.VERIFIED),
    ]


async def test_loi_ghi_audit_log_khong_chan_nghiep_vu(  # S03-02, api-conventions §8
    client: AsyncClient, db_session: Session, tutor, create_profile, monkeypatch
) -> None:
    profile = await create_profile(tutor)
    await client.post(
        f"/api/tutor-profiles/{profile['id']}/evidences",
        files={"files": ("bang-diem.pdf", b"%PDF-1.4 test", "application/pdf")},
        headers=tutor.headers,
    )

    def broken_audit(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("Lỗi ghi audit_logs giả lập")

    monkeypatch.setattr(AuditLogRepository, "record_transition", broken_audit)

    submitted = await client.post(
        f"/api/tutor-profiles/{profile['id']}/submit", headers=tutor.headers
    )
    assert submitted.status_code == 200
    assert submitted.json()["data"]["status"] == "PendingReview"

    logs = list(
        db_session.scalars(
            select(AuditLog).where(
                AuditLog.entity == "TutorProfile",
                AuditLog.entity_id == UUID(profile["id"]),
                AuditLog.to_status == "PendingReview",
            )
        )
    )
    assert logs == []


def test_list_for_entity_sap_xep_theo_thoi_gian_tang_dan(db_session: Session, make_account) -> None:
    actor = make_account(1)
    entity_id = UUID("11111111-1111-1111-1111-111111111111")
    t0 = datetime(2026, 11, 20, 8, 0, tzinfo=timezone.utc)
    service = AuditLogService(AuditLogRepository(db_session))

    assert service.record_transition(
        actor_id=actor.user_id,
        entity="TutorProfile",
        entity_id=entity_id,
        action="Submit",
        from_status="Draft",
        to_status="PendingReview",
        created_at=t0 + timedelta(minutes=5),
    )
    assert service.record_transition(
        actor_id=actor.user_id,
        entity="TutorProfile",
        entity_id=entity_id,
        action="Create",
        from_status=None,
        to_status="Draft",
        created_at=t0,
    )
    db_session.commit()

    logs = service.list_for_entity("TutorProfile", entity_id)
    assert [(log.action, log.from_status, log.to_status) for log in logs] == [
        ("Create", None, "Draft"),
        ("Submit", "Draft", "PendingReview"),
    ]

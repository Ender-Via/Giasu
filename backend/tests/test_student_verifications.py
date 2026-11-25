from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.constants import NotificationType, VerificationStatus
from app.core.file_validation import MAX_EVIDENCE_BYTES
from app.db.models import StudentVerification, Tutor
from tests.fakes import DOCX_BYTES, JPEG_BYTES, PDF_BYTES

pytestmark = pytest.mark.anyio

VALID_FORM = {
    "university": "Trường Đại học Công nghệ Thông tin – ĐHQG-HCM",
    "studentCode": "22520001",
}


async def _submit_valid(client: AsyncClient, tutor, **form_overrides: str):  # type: ignore[no-untyped-def]
    data = {**VALID_FORM, **form_overrides}
    return await client.post(
        "/api/student-verifications",
        data=data,
        files={"file": ("the-sv.jpg", JPEG_BYTES, "image/jpeg")},
        headers=tutor.headers,
    )


async def test_gia_su_gui_yeu_cau_xac_thuc_va_admin_nhan_thong_bao(  # AC-VERIFY-01
    client: AsyncClient, db_session: Session, make_account, tutor
) -> None:
    admin_1 = make_account(1)
    admin_2 = make_account(1)

    response = await _submit_valid(client, tutor)
    mine = await client.get("/api/student-verifications/mine", headers=tutor.headers)

    assert response.status_code == 201
    created = response.json()["data"]
    assert created["status"] == VerificationStatus.PENDING
    assert created["studentCode"] == "22520001"
    assert mine.status_code == 200
    assert mine.json()["data"]["id"] == created["id"]
    assert "evidenceUrl" not in mine.json()["data"]

    tutor_row = db_session.get(Tutor, tutor.user_id)
    assert tutor_row is not None
    assert tutor_row.verification_status == VerificationStatus.PENDING

    for admin in (admin_1, admin_2):
        notis = await client.get("/api/notifications", headers=admin.headers)
        assert notis.json()["data"]["totalCount"] == 1
        assert notis.json()["data"]["items"][0]["type"] == NotificationType.MODERATION_QUEUE


async def test_khong_gui_trung_khi_dang_pending_hoac_da_verified(  # AC-VERIFY-02
    client: AsyncClient, make_account, tutor
) -> None:
    admin = make_account(1)
    first = await _submit_valid(client, tutor)
    assert first.status_code == 201

    duplicate_pending = await _submit_valid(client, tutor)
    assert duplicate_pending.status_code == 409

    verification_id = first.json()["data"]["id"]
    approved = await client.post(
        f"/api/student-verifications/{verification_id}/approve", headers=admin.headers
    )
    assert approved.status_code == 200

    duplicate_verified = await _submit_valid(client, tutor)
    assert duplicate_verified.status_code == 409


async def test_tep_hoac_du_lieu_khong_hop_le_bi_chan_400_khong_luu_storage(  # AC-VERIFY-03
    client: AsyncClient, tutor, storage
) -> None:
    too_large = await client.post(
        "/api/student-verifications",
        data=VALID_FORM,
        files={"file": ("lon.jpg", b"\xff\xd8\xff\xe0" + b"0" * MAX_EVIDENCE_BYTES, "image/jpeg")},
        headers=tutor.headers,
    )
    bad_type = await client.post(
        "/api/student-verifications",
        data=VALID_FORM,
        files={"file": ("giay.docx", DOCX_BYTES, "application/octet-stream")},
        headers=tutor.headers,
    )
    missing_file = await client.post(
        "/api/student-verifications",
        data=VALID_FORM,
        headers=tutor.headers,
    )
    bad_code = await client.post(
        "/api/student-verifications",
        data={"university": "ĐH Bách Khoa", "studentCode": "22-52!"},
        files={"file": ("the.pdf", PDF_BYTES, "application/pdf")},
        headers=tutor.headers,
    )

    assert too_large.status_code == 400
    assert bad_type.status_code == 400
    assert missing_file.status_code == 400
    assert bad_code.status_code == 400
    assert storage.objects == {}


async def test_admin_xem_chi_tiet_co_url_ky_60_phut_va_duyet(  # AC-VERIFY-04
    client: AsyncClient, db_session: Session, make_account, tutor
) -> None:
    admin = make_account(1)
    created = await _submit_valid(client, tutor)
    verification_id = created.json()["data"]["id"]

    detail = await client.get(
        f"/api/student-verifications/{verification_id}", headers=admin.headers
    )
    assert detail.status_code == 200
    detail_data = detail.json()["data"]
    assert detail_data["evidenceUrl"].endswith("expiresIn=3600")
    assert "evidenceFileRef" not in detail_data

    approved = await client.post(
        f"/api/student-verifications/{verification_id}/approve", headers=admin.headers
    )
    assert approved.status_code == 200
    assert approved.json()["data"]["status"] == VerificationStatus.VERIFIED

    db_session.expire_all()
    tutor_row = db_session.get(Tutor, tutor.user_id)
    assert tutor_row is not None
    assert tutor_row.verification_status == VerificationStatus.VERIFIED

    tutor_noti = await client.get("/api/notifications", headers=tutor.headers)
    assert tutor_noti.json()["data"]["totalCount"] == 1
    assert tutor_noti.json()["data"]["items"][0]["type"] == NotificationType.MODERATION_RESULT


async def test_admin_tu_choi_bat_buoc_ly_do_va_gia_su_gui_lai_duoc(  # AC-VERIFY-05
    client: AsyncClient, make_account, tutor
) -> None:
    admin = make_account(1)
    created = await _submit_valid(client, tutor)
    verification_id = created.json()["data"]["id"]

    empty_reason = await client.post(
        f"/api/student-verifications/{verification_id}/reject",
        json={"reason": "   "},
        headers=admin.headers,
    )
    too_long_reason = await client.post(
        f"/api/student-verifications/{verification_id}/reject",
        json={"reason": "a" * 501},
        headers=admin.headers,
    )
    assert empty_reason.status_code == 400
    assert too_long_reason.status_code == 400

    still_mine = await client.get("/api/student-verifications/mine", headers=tutor.headers)
    assert still_mine.json()["data"]["status"] == VerificationStatus.PENDING

    rejected = await client.post(
        f"/api/student-verifications/{verification_id}/reject",
        json={"reason": "Ảnh thẻ bị che mất mã số sinh viên."},
        headers=admin.headers,
    )
    assert rejected.status_code == 200
    assert rejected.json()["data"]["status"] == VerificationStatus.REJECTED

    mine_after_reject = await client.get(
        "/api/student-verifications/mine", headers=tutor.headers
    )
    assert mine_after_reject.json()["data"]["status"] == VerificationStatus.REJECTED
    assert (
        mine_after_reject.json()["data"]["rejectReason"]
        == "Ảnh thẻ bị che mất mã số sinh viên."
    )

    resubmitted = await _submit_valid(client, tutor, studentCode="22520002")
    assert resubmitted.status_code == 201
    assert resubmitted.json()["data"]["status"] == VerificationStatus.PENDING


async def test_phan_quyen_va_xung_dot_trang_thai(  # AC-VERIFY-06
    client: AsyncClient, make_account, tutor, other_tutor
) -> None:
    admin = make_account(1)
    parent = make_account(3)
    created = await _submit_valid(client, other_tutor)
    verification_id = created.json()["data"]["id"]

    tutor_call_admin = await client.get(
        f"/api/student-verifications/{verification_id}", headers=tutor.headers
    )
    parent_submit = await client.post(
        "/api/student-verifications",
        data=VALID_FORM,
        files={"file": ("the.jpg", JPEG_BYTES, "image/jpeg")},
        headers=parent.headers,
    )
    assert tutor_call_admin.status_code == 403
    assert parent_submit.status_code == 403

    await client.post(
        f"/api/student-verifications/{verification_id}/approve", headers=admin.headers
    )
    approve_again = await client.post(
        f"/api/student-verifications/{verification_id}/approve", headers=admin.headers
    )
    not_found = await client.get(
        f"/api/student-verifications/{uuid4()}", headers=admin.headers
    )
    assert approve_again.status_code == 409
    assert not_found.status_code == 404


async def test_gia_su_chi_thay_yeu_cau_cua_minh(  # AC-VERIFY-07
    client: AsyncClient, make_account
) -> None:
    admin = make_account(1)
    tutor_a = make_account(2)
    tutor_b = make_account(2)
    tutor_c = make_account(2)

    sub_a = await _submit_valid(client, tutor_a, studentCode="22520010")
    await client.post(
        f"/api/student-verifications/{sub_a.json()['data']['id']}/reject",
        json={"reason": "Mờ ảnh"},
        headers=admin.headers,
    )
    sub_b = await _submit_valid(client, tutor_b, studentCode="22520020")

    mine_a = await client.get("/api/student-verifications/mine", headers=tutor_a.headers)
    mine_b = await client.get("/api/student-verifications/mine", headers=tutor_b.headers)
    mine_c = await client.get("/api/student-verifications/mine", headers=tutor_c.headers)

    assert mine_a.json()["data"]["status"] == VerificationStatus.REJECTED
    assert mine_a.json()["data"]["rejectReason"] == "Mờ ảnh"
    assert mine_b.json()["data"]["id"] == sub_b.json()["data"]["id"]
    assert mine_b.json()["data"]["status"] == VerificationStatus.PENDING
    assert mine_c.status_code == 200
    assert mine_c.json()["data"] is None


async def test_admin_danh_sach_pending_cu_nhat_truoc_va_don_storage_khi_trung(
    client: AsyncClient, db_session: Session, make_account, tutor, other_tutor, storage
) -> None:
    admin = make_account(1)
    t1 = await _submit_valid(client, tutor, studentCode="22520001")
    t2 = await _submit_valid(client, other_tutor, studentCode="22520002")

    first_row = db_session.get(StudentVerification, UUID(t1.json()["data"]["id"]))
    second_row = db_session.get(StudentVerification, UUID(t2.json()["data"]["id"]))
    assert first_row is not None and second_row is not None
    first_row.created_at = datetime(2026, 11, 20, 8, 0, tzinfo=timezone.utc)
    second_row.created_at = first_row.created_at + timedelta(hours=1)
    db_session.commit()

    listed = await client.get(
        "/api/student-verifications?status=Pending&page=1&pageSize=20", headers=admin.headers
    )
    assert listed.status_code == 200
    ids = [item["id"] for item in listed.json()["data"]["items"]]
    assert ids == [t1.json()["data"]["id"], t2.json()["data"]["id"]]

    tutor_3 = make_account(2)
    def insert_pending_concurrently() -> None:
        db_session.add(
            StudentVerification(
                id=uuid4(),
                tutor_id=tutor_3.user_id,
                university="ĐH Khoa học Tự nhiên",
                student_code="22520099",
                evidence_file_ref=f"student-verifications/{tutor_3.user_id}/race.jpg",
                status=VerificationStatus.PENDING,
                created_at=datetime.now(timezone.utc),
            )
        )
        db_session.commit()

    storage.on_upload = insert_pending_concurrently
    race = await _submit_valid(client, tutor_3, studentCode="22520099")
    assert race.status_code == 409
    assert len(storage.deleted) == 1
    assert storage.deleted[0] not in storage.objects
    assert len(storage.objects) == 2

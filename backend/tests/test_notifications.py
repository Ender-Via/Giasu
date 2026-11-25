import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.constants import NotificationType
from app.core.email_sender import LoggingEmailSender
from app.db.models import Notification
from app.repositories.notifications import NotificationRepository
from app.services.notifications import NotificationService
from tests.fakes import PDF_BYTES

pytestmark = pytest.mark.anyio


def _seed_notifications(
    db_session: Session,
    recipient_id: UUID,
    count: int,
    *,
    unread_count: int,
    prefix: str = "Thông báo",
) -> list[Notification]:
    base_time = datetime(2026, 11, 20, 8, 0, tzinfo=timezone.utc)
    items: list[Notification] = []
    for index in range(count):
        item = Notification(
            id=uuid4(),
            recipient_id=recipient_id,
            type=NotificationType.MODERATION_RESULT,
            title=f"{prefix} #{index + 1}",
            message=f"Nội dung {prefix} #{index + 1}",
            link="/tutor/profiles",
            is_read=index >= unread_count,
            created_at=base_time + timedelta(minutes=index),
        )
        db_session.add(item)
        items.append(item)
    db_session.commit()
    return items


async def test_xem_danh_sach_va_loc_chua_doc_chi_cua_minh(  # AC-NOTI-01
    client: AsyncClient, db_session: Session, tutor, other_tutor
) -> None:
    _seed_notifications(db_session, tutor.user_id, 25, unread_count=3, prefix="Gia sư A")
    _seed_notifications(db_session, other_tutor.user_id, 4, unread_count=4, prefix="Gia sư B")

    page_1 = await client.get("/api/notifications?page=1&pageSize=20", headers=tutor.headers)
    unread_only = await client.get(
        "/api/notifications?unreadOnly=true&page=1&pageSize=20", headers=tutor.headers
    )

    assert page_1.status_code == unread_only.status_code == 200
    page_data = page_1.json()["data"]
    assert page_data["totalCount"] == 25
    assert page_data["page"] == 1
    assert page_data["pageSize"] == 20
    assert len(page_data["items"]) == 20
    assert page_data["items"][0]["title"] == "Gia sư A #25"
    assert all("Gia sư B" not in item["title"] for item in page_data["items"])

    unread_data = unread_only.json()["data"]
    assert unread_data["totalCount"] == 3
    assert [item["title"] for item in unread_data["items"]] == [
        "Gia sư A #3",
        "Gia sư A #2",
        "Gia sư A #1",
    ]


async def test_danh_dau_da_doc_va_da_doc_tat_ca(  # AC-NOTI-02
    client: AsyncClient, db_session: Session, tutor
) -> None:
    seeded = _seed_notifications(db_session, tutor.user_id, 3, unread_count=3)

    initial_count = await client.get("/api/notifications/unread-count", headers=tutor.headers)
    mark_one = await client.post(
        f"/api/notifications/{seeded[0].id}/read", headers=tutor.headers
    )
    after_one = await client.get("/api/notifications/unread-count", headers=tutor.headers)
    mark_all = await client.post("/api/notifications/read-all", headers=tutor.headers)
    after_all = await client.get("/api/notifications/unread-count", headers=tutor.headers)

    assert initial_count.json()["data"]["count"] == 3
    assert mark_one.status_code == 200
    assert after_one.json()["data"]["count"] == 2
    assert mark_all.status_code == 200
    assert after_all.json()["data"]["count"] == 0


async def test_danh_dau_thong_bao_cua_nguoi_khac_tra_404(  # AC-NOTI-03
    client: AsyncClient, db_session: Session, tutor, other_tutor
) -> None:
    other_items = _seed_notifications(db_session, other_tutor.user_id, 1, unread_count=1)

    response = await client.post(
        f"/api/notifications/{other_items[0].id}/read", headers=tutor.headers
    )

    assert response.status_code == 404
    assert response.json()["message"] == "Không tìm thấy thông báo."
    db_session.expire_all()
    refreshed = db_session.get(Notification, other_items[0].id)
    assert refreshed is not None
    assert refreshed.is_read is False


async def test_tat_email_mot_loai_van_co_thong_bao_nhung_khong_log_email(  # AC-NOTI-04
    client: AsyncClient,
    db_session: Session,
    tutor,
    caplog: pytest.LogCaptureFixture,
) -> None:
    disable = await client.put(
        "/api/notification-preferences",
        json={"items": [{"type": NotificationType.MODERATION_RESULT, "emailEnabled": False}]},
        headers=tutor.headers,
    )
    assert disable.status_code == 200

    service = NotificationService(NotificationRepository(db_session), LoggingEmailSender())
    with caplog.at_level(logging.INFO, logger="app.core.email_sender"):
        service.notify(
            tutor.user_id,
            NotificationType.MODERATION_RESULT,
            "Hồ sơ bị từ chối",
            "Vui lòng bổ sung minh chứng.",
            link="/tutor/profiles",
        )
    assert caplog.records == []

    listed = await client.get("/api/notifications", headers=tutor.headers)
    assert listed.json()["data"]["totalCount"] == 1
    assert listed.json()["data"]["items"][0]["title"] == "Hồ sơ bị từ chối"

    enable = await client.put(
        "/api/notification-preferences",
        json={"items": [{"type": NotificationType.MODERATION_RESULT, "emailEnabled": True}]},
        headers=tutor.headers,
    )
    assert enable.status_code == 200

    with caplog.at_level(logging.INFO, logger="app.core.email_sender"):
        service.notify(
            tutor.user_id,
            NotificationType.MODERATION_RESULT,
            "Hồ sơ đã được duyệt",
            "Hồ sơ của bạn đã hiển thị.",
            link="/tutor/profiles",
        )
    assert len(caplog.records) == 1
    assert "ModerationResult" in caplog.records[0].message


async def test_cau_hinh_email_khong_hop_le_tra_400_giu_nguyen_cau_hinh_cu(  # AC-NOTI-05
    client: AsyncClient, tutor
) -> None:
    setup = await client.put(
        "/api/notification-preferences",
        json={"items": [{"type": NotificationType.SESSION, "emailEnabled": False}]},
        headers=tutor.headers,
    )
    assert setup.status_code == 200

    invalid_unknown = await client.put(
        "/api/notification-preferences",
        json={"items": [{"type": "Abc", "emailEnabled": False}]},
        headers=tutor.headers,
    )
    invalid_role_type = await client.put(
        "/api/notification-preferences",
        json={"items": [{"type": NotificationType.MODERATION_QUEUE, "emailEnabled": False}]},
        headers=tutor.headers,
    )

    assert invalid_unknown.status_code == 400
    assert invalid_role_type.status_code == 400

    current = await client.get("/api/notification-preferences", headers=tutor.headers)
    by_type = {item["type"]: item["emailEnabled"] for item in current.json()["data"]["items"]}
    assert by_type[NotificationType.SESSION] is False
    assert by_type[NotificationType.MODERATION_RESULT] is True
    assert NotificationType.MODERATION_QUEUE not in by_type


async def test_chua_dang_nhap_khong_truy_cap_duoc_thong_bao(client: AsyncClient) -> None:
    response = await client.get("/api/notifications")
    assert response.status_code == 401


async def test_gui_duyet_ho_so_tao_thong_bao_cho_admin(  # AC-PROFILE-07
    client: AsyncClient, make_account, tutor, create_profile
) -> None:
    admin = make_account(1)
    profile = await create_profile(tutor)
    await client.post(
        f"/api/tutor-profiles/{profile['id']}/evidences",
        files={"files": ("bang-diem.pdf", PDF_BYTES, "application/pdf")},
        headers=tutor.headers,
    )

    submitted = await client.post(
        f"/api/tutor-profiles/{profile['id']}/submit", headers=tutor.headers
    )
    assert submitted.status_code == 200

    admin_noti = await client.get("/api/notifications", headers=admin.headers)
    assert admin_noti.json()["data"]["totalCount"] == 1
    item = admin_noti.json()["data"]["items"][0]
    assert item["type"] == NotificationType.MODERATION_QUEUE
    assert item["link"] == "/admin/tutor-profiles"

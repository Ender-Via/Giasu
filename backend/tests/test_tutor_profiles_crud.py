from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.profile_fixtures import valid_profile_payload

pytestmark = pytest.mark.anyio


async def test_tao_ho_so_dau_tien_la_nhap_dang_nhan_day_va_mac_dinh(  # AC-PROFILE-01
    client: AsyncClient, tutor
) -> None:
    response = await client.post(
        "/api/tutor-profiles", json=valid_profile_payload(), headers=tutor.headers
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["status"] == "Draft"
    assert data["availability"] == "Accepting"
    assert data["isDefault"] is True
    assert [s["name"] for s in data["subjects"]] == ["Toán", "Tiếng Anh"]
    assert data["teachingWards"] == ["Phường Bến Thành", "Phường Sài Gòn"]
    assert data["evidenceCount"] == 0
    assert data["createdAtUtc"].endswith("Z")


async def test_client_khong_tu_dat_trang_thai_hay_mac_dinh(  # CC-04
    client: AsyncClient, tutor, create_profile
) -> None:
    await create_profile(tutor)
    response = await client.post(
        "/api/tutor-profiles",
        json=valid_profile_payload(status="Approved", isDefault=True, tutorId=str(uuid4())),
        headers=tutor.headers,
    )

    data = response.json()["data"]
    assert (data["status"], data["isDefault"]) == ("Draft", False)


async def test_co_4_ho_so_tao_duoc_co_5_thi_409(  # AC-PROFILE-02, BR-23
    client: AsyncClient, tutor, create_profile
) -> None:
    for _ in range(4):
        await create_profile(tutor)
    fifth = await client.post(
        "/api/tutor-profiles", json=valid_profile_payload(), headers=tutor.headers
    )
    sixth = await client.post(
        "/api/tutor-profiles", json=valid_profile_payload(), headers=tutor.headers
    )

    assert fifth.status_code == 201
    assert sixth.status_code == 409
    assert sixth.json()["message"] == "Bạn đã có 5 hồ sơ, không tạo thêm được."
    mine = await client.get("/api/tutor-profiles/mine", headers=tutor.headers)
    assert len(mine.json()["data"]) == 5


async def test_mon_khong_co_trong_danh_muc_thi_400(client: AsyncClient, tutor) -> None:  # BR-24
    response = await client.post(
        "/api/tutor-profiles", json=valid_profile_payload(subjectIds=[1, 99]), headers=tutor.headers
    )

    assert response.status_code == 400
    assert response.json()["errors"] == ["Môn học không hợp lệ."]


async def test_gia_su_chua_co_dong_tutors_thi_khong_tao_duoc(  # BR-SCOPE-02
    client: AsyncClient, make_account, subjects
) -> None:
    account = make_account(2, with_role_row=False)
    response = await client.post(
        "/api/tutor-profiles", json=valid_profile_payload(), headers=account.headers
    )

    assert response.status_code == 404


async def test_danh_sach_mac_dinh_truoc_roi_moi_cap_nhat_truoc(  # SCR-TUT-01
    client: AsyncClient, tutor, other_tutor, create_profile
) -> None:
    first = await create_profile(tutor, title="[TEST] Hồ sơ thứ nhất")
    second = await create_profile(tutor, title="[TEST] Hồ sơ thứ hai")
    await create_profile(other_tutor)
    await client.put(
        f"/api/tutor-profiles/{second['id']}",
        json=valid_profile_payload(title="[TEST] Hồ sơ thứ hai đã sửa"),
        headers=tutor.headers,
    )

    response = await client.get("/api/tutor-profiles/mine", headers=tutor.headers)

    ids = [item["id"] for item in response.json()["data"]]
    assert ids == [first["id"], second["id"]]


async def test_ho_so_nguoi_khac_tra_404_cung_mot_cau(  # AC-PROFILE-04, BR-SCOPE-05
    client: AsyncClient, tutor, other_tutor, create_profile
) -> None:
    profile = await create_profile(other_tutor)
    base = f"/api/tutor-profiles/{profile['id']}"
    calls = [
        client.get(base, headers=tutor.headers),
        client.put(base, json=valid_profile_payload(), headers=tutor.headers),
        client.post(f"{base}/set-default", headers=tutor.headers),
        client.post(f"{base}/submit", headers=tutor.headers),
        client.put(f"{base}/availability", json={"availability": "Full"}, headers=tutor.headers),
    ]

    for call in calls:
        response = await call
        assert response.status_code == 404
        assert response.json()["message"] == "Không tìm thấy hồ sơ."
    unchanged = await client.get(base, headers=other_tutor.headers)
    assert unchanged.json()["data"]["title"] == profile["title"]


async def test_sua_ho_so_nhap_giu_nhap_va_cap_nhat_noi_dung(  # FR-03
    client: AsyncClient, tutor, create_profile
) -> None:
    profile = await create_profile(tutor)
    response = await client.put(
        f"/api/tutor-profiles/{profile['id']}",
        json=valid_profile_payload(teachingMode="Online", subjectIds=[2]),
        headers=tutor.headers,
    )

    data = response.json()["data"]
    assert response.status_code == 200
    assert (data["status"], data["teachingMode"], data["teachingWards"]) == ("Draft", "Online", [])
    assert [s["id"] for s in data["subjects"]] == [2]


async def test_sua_ho_so_dang_cho_duyet_thi_409(  # AC-PROFILE-07, FR-03
    client: AsyncClient, tutor, create_profile, set_status
) -> None:
    profile = await create_profile(tutor)
    set_status(profile["id"], "PendingReview")

    response = await client.put(
        f"/api/tutor-profiles/{profile['id']}", json=valid_profile_payload(), headers=tutor.headers
    )

    assert response.status_code == 409
    assert response.json()["message"] == "Hồ sơ đang chờ duyệt, chưa sửa được."

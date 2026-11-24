import pytest
from httpx import AsyncClient

from tests.fakes import PDF_BYTES

pytestmark = pytest.mark.anyio


async def upload_pdf(client: AsyncClient, account, profile_id: str):  # type: ignore[no-untyped-def]
    return await client.post(
        f"/api/tutor-profiles/{profile_id}/evidences",
        files={"files": ("bang-diem.pdf", PDF_BYTES, "application/pdf")},
        headers=account.headers,
    )


async def test_dat_mac_dinh_ho_so_khac_bo_mac_dinh_ho_so_cu(  # AC-PROFILE-03, BR-02
    client: AsyncClient, tutor, create_profile
) -> None:
    first = await create_profile(tutor)
    second = await create_profile(tutor)

    response = await client.post(
        f"/api/tutor-profiles/{second['id']}/set-default", headers=tutor.headers
    )
    again = await client.post(
        f"/api/tutor-profiles/{second['id']}/set-default", headers=tutor.headers
    )

    assert response.status_code == again.status_code == 200
    mine = (await client.get("/api/tutor-profiles/mine", headers=tutor.headers)).json()["data"]
    defaults = {item["id"]: item["isDefault"] for item in mine}
    assert defaults == {first["id"]: False, second["id"]: True}


async def test_dat_mac_dinh_khong_lam_ho_so_da_duyet_phai_duyet_lai(  # BR-25
    client: AsyncClient, tutor, create_profile, set_status
) -> None:
    await create_profile(tutor)
    second = await create_profile(tutor)
    set_status(second["id"], "Approved")

    response = await client.post(
        f"/api/tutor-profiles/{second['id']}/set-default", headers=tutor.headers
    )

    assert response.json()["data"]["status"] == "Approved"


async def test_doi_trang_thai_nhan_day(  # AC-PROFILE-09, FR-36
    client: AsyncClient, tutor, create_profile
) -> None:
    profile = await create_profile(tutor)
    url = f"/api/tutor-profiles/{profile['id']}/availability"

    full = await client.put(url, json={"availability": "Full"}, headers=tutor.headers)
    paused = await client.put(url, json={"availability": "Paused"}, headers=tutor.headers)
    busy = await client.put(url, json={"availability": "Busy"}, headers=tutor.headers)

    assert (full.status_code, paused.status_code) == (200, 200)
    assert paused.json()["data"]["availability"] == "Paused"
    assert busy.status_code == 400
    assert busy.json()["errors"] == ["Trạng thái nhận dạy không hợp lệ."]


async def test_doi_nhan_day_tren_ho_so_da_duyet_van_da_duyet(  # AC-PROFILE-08 (b), BR-25
    client: AsyncClient, tutor, create_profile, set_status
) -> None:
    profile = await create_profile(tutor)
    set_status(profile["id"], "Approved")

    response = await client.put(
        f"/api/tutor-profiles/{profile['id']}/availability",
        json={"availability": "Full"},
        headers=tutor.headers,
    )

    assert response.json()["data"]["status"] == "Approved"


async def test_gui_duyet_khi_chua_co_minh_chung_thi_bi_tu_choi(  # AC-PROFILE-06, BR-04
    client: AsyncClient, tutor, create_profile
) -> None:
    profile = await create_profile(tutor, description=None)

    response = await client.post(
        f"/api/tutor-profiles/{profile['id']}/submit", headers=tutor.headers
    )

    assert response.status_code == 400
    assert response.json()["errors"] == [
        "Hồ sơ cần phần giới thiệu, kinh nghiệm.",
        "Hồ sơ cần ít nhất một minh chứng.",
    ]
    after = await client.get(f"/api/tutor-profiles/{profile['id']}", headers=tutor.headers)
    assert after.json()["data"]["status"] == "Draft"


async def test_gui_duyet_thanh_cong_roi_khoa_sua_va_minh_chung(  # AC-PROFILE-07, BR-25, BR-26
    client: AsyncClient, tutor, create_profile
) -> None:
    profile = await create_profile(tutor)
    await upload_pdf(client, tutor, profile["id"])

    submitted = await client.post(
        f"/api/tutor-profiles/{profile['id']}/submit", headers=tutor.headers
    )
    edit = await client.put(
        f"/api/tutor-profiles/{profile['id']}",
        json={**profile, "subjectIds": [1], "title": "[TEST] Tiêu đề đã đổi sau gửi"},
        headers=tutor.headers,
    )
    add_evidence = await upload_pdf(client, tutor, profile["id"])
    submit_again = await client.post(
        f"/api/tutor-profiles/{profile['id']}/submit", headers=tutor.headers
    )

    assert submitted.status_code == 200
    assert submitted.json()["data"]["status"] == "PendingReview"
    assert submitted.json()["data"]["submittedAtUtc"] is not None
    assert (edit.status_code, add_evidence.status_code, submit_again.status_code) == (409, 409, 409)


async def test_gui_lai_ho_so_bi_tu_choi_xoa_ly_do_cu(  # FR-04, business-rules §2.1
    client: AsyncClient, tutor, create_profile, set_status
) -> None:
    profile = await create_profile(tutor)
    await upload_pdf(client, tutor, profile["id"])
    set_status(profile["id"], "Rejected", "Minh chứng mờ, không đọc được.")

    rejected = await client.get(f"/api/tutor-profiles/{profile['id']}", headers=tutor.headers)
    resubmitted = await client.post(
        f"/api/tutor-profiles/{profile['id']}/submit", headers=tutor.headers
    )

    assert rejected.json()["data"]["rejectReason"] == "Minh chứng mờ, không đọc được."
    assert resubmitted.json()["data"]["status"] == "PendingReview"
    assert resubmitted.json()["data"]["rejectReason"] is None


async def test_gui_duyet_ho_so_da_duyet_thi_409(  # FR-04
    client: AsyncClient, tutor, create_profile, set_status
) -> None:
    profile = await create_profile(tutor)
    set_status(profile["id"], "Approved")

    response = await client.post(
        f"/api/tutor-profiles/{profile['id']}/submit", headers=tutor.headers
    )

    assert response.status_code == 409
    assert (
        response.json()["message"] == "Chỉ gửi duyệt được hồ sơ ở trạng thái Nháp hoặc Bị từ chối."
    )

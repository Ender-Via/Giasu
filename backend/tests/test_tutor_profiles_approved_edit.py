import pytest
from httpx import AsyncClient

from tests.profile_fixtures import valid_profile_payload

pytestmark = pytest.mark.anyio


async def test_sua_ho_so_da_duyet_thi_ve_cho_duyet(  # AC-PROFILE-08 (a), BR-25
    client: AsyncClient, tutor, create_profile, set_status, storage
) -> None:
    profile = await create_profile(tutor)
    files = {"files": ("bang-diem.pdf", b"%PDF-1.7 noi dung", "application/pdf")}
    await client.post(
        f"/api/tutor-profiles/{profile['id']}/evidences", files=files, headers=tutor.headers
    )
    set_status(profile["id"], "Approved")

    response = await client.put(
        f"/api/tutor-profiles/{profile['id']}",
        json=valid_profile_payload(expectedFeePerSession=250_000),
        headers=tutor.headers,
    )

    data = response.json()["data"]
    assert (data["status"], data["expectedFeePerSession"]) == ("PendingReview", 250_000)
    assert data["submittedAtUtc"] is not None


async def test_luu_ho_so_da_duyet_khong_doi_gi_thi_van_da_duyet(  # BR-25
    client: AsyncClient, tutor, create_profile, set_status
) -> None:
    profile = await create_profile(tutor)
    set_status(profile["id"], "Approved")

    response = await client.put(
        f"/api/tutor-profiles/{profile['id']}", json=valid_profile_payload(), headers=tutor.headers
    )

    assert response.json()["data"]["status"] == "Approved"


async def test_sua_ho_so_da_duyet_ma_xoa_gioi_thieu_thi_400_va_khong_doi(  # BR-04, BR-25
    client: AsyncClient, tutor, create_profile, set_status
) -> None:
    profile = await create_profile(tutor)
    set_status(profile["id"], "Approved")

    response = await client.put(
        f"/api/tutor-profiles/{profile['id']}",
        json=valid_profile_payload(description=None),
        headers=tutor.headers,
    )

    assert response.status_code == 400
    assert "Hồ sơ cần phần giới thiệu, kinh nghiệm." in response.json()["errors"]
    after = await client.get(f"/api/tutor-profiles/{profile['id']}", headers=tutor.headers)
    assert after.json()["data"]["status"] == "Approved"
    assert after.json()["data"]["description"] == profile["description"]


async def test_luu_lai_cung_cac_mon_theo_thu_tu_khac_van_da_duyet(  # BR-25
    client: AsyncClient, tutor, create_profile, set_status
) -> None:
    profile = await create_profile(tutor, subjectIds=[4, 1])
    set_status(profile["id"], "Approved")

    response = await client.put(
        f"/api/tutor-profiles/{profile['id']}",
        json=valid_profile_payload(subjectIds=[4, 1]),
        headers=tutor.headers,
    )

    data = response.json()["data"]
    assert data["status"] == "Approved"
    assert [s["id"] for s in profile["subjects"]] == [s["id"] for s in data["subjects"]] == [1, 4]

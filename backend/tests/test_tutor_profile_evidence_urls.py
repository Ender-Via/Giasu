import pytest
from httpx import AsyncClient

from tests.fakes import PDF_BYTES

pytestmark = pytest.mark.anyio


def evidence_url(profile_id: str) -> str:
    return f"/api/tutor-profiles/{profile_id}/evidences"


async def test_chi_tiet_tra_url_ky_va_khong_lo_duong_dan_bucket(  # D16
    client: AsyncClient, tutor, create_profile
) -> None:
    profile = await create_profile(tutor)
    await client.post(
        evidence_url(profile["id"]),
        files={"files": ("C:\\Users\\sv\\bang-diem.pdf", PDF_BYTES, "application/pdf")},
        headers=tutor.headers,
    )

    detail = await client.get(f"/api/tutor-profiles/{profile['id']}", headers=tutor.headers)
    evidence = detail.json()["data"]["evidences"][0]

    assert evidence["fileName"] == "bang-diem.pdf"
    assert evidence["url"].endswith("expiresIn=3600")
    assert "fileRef" not in evidence


async def test_storage_khong_ky_duoc_url_van_xem_duoc_ho_so(  # D16
    client: AsyncClient, tutor, create_profile, storage
) -> None:
    profile = await create_profile(tutor)
    await client.post(
        evidence_url(profile["id"]),
        files={"files": ("bang-diem.pdf", PDF_BYTES, "application/pdf")},
        headers=tutor.headers,
    )
    storage.fail_signing = True

    detail = await client.get(f"/api/tutor-profiles/{profile['id']}", headers=tutor.headers)

    assert detail.status_code == 200
    assert detail.json()["data"]["evidences"][0]["url"] is None


async def test_body_qua_lon_bi_chan_truoc_khi_doc(client: AsyncClient, tutor) -> None:
    response = await client.post(
        "/api/tutor-profiles/00000000-0000-0000-0000-000000000000/evidences",
        content=b"x",
        headers={
            **tutor.headers,
            "Content-Length": str(27 * 1024 * 1024),
            "Origin": "http://localhost:3000",
        },
    )

    assert response.status_code == 413
    assert response.json()["message"] == "Dữ liệu gửi lên quá lớn."
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert response.headers["x-content-type-options"] == "nosniff"


async def test_body_chunked_qua_lon_bi_chan_ca_khi_chua_dang_nhap(client: AsyncClient) -> None:
    async def chunks():  # type: ignore[no-untyped-def]
        yield (
            b'--x\r\nContent-Disposition: form-data; name="files"; filename="a.pdf"\r\n'
            b"Content-Type: application/pdf\r\n\r\n%PDF-"
        )
        for _ in range(27):
            yield b"0" * (1024 * 1024)

    response = await client.post(
        "/api/tutor-profiles/00000000-0000-0000-0000-000000000000/evidences",
        content=chunks(),
        headers={
            "Content-Type": "multipart/form-data; boundary=x",
            "Origin": "http://localhost:3000",
        },
    )

    assert "content-length" not in response.request.headers
    assert response.status_code == 413
    assert response.json()["message"] == "Dữ liệu gửi lên quá lớn."
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

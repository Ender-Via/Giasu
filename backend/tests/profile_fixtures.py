from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.db.models import Parent, Subject, Tutor, TutorProfile

SUBJECT_NAMES = ("Toán", "Tiếng Việt", "Ngữ văn", "Tiếng Anh", "Vật lý", "Hóa học")


@dataclass
class Account:
    user_id: UUID
    headers: dict[str, str]


def valid_profile_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "title": "[TEST] Toán THPT luyện thi đại học",
        "subjectIds": [1, 4],
        "educationLevel": "UpperSecondary",
        "teachingMode": "Both",
        "province": "TP. Hồ Chí Minh",
        "teachingWards": ["Phường Bến Thành", "Phường Sài Gòn"],
        "expectedFeePerSession": 200_000,
        "description": "Sinh viên năm 3, 2 năm kinh nghiệm dạy Toán THPT.",
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def subjects(db_session: Session) -> list[Subject]:
    items = [Subject(id=index, name=name) for index, name in enumerate(SUBJECT_NAMES, start=1)]
    db_session.add_all(items)
    db_session.commit()
    return items


@pytest.fixture
def make_account(db_session: Session, add_user, make_token):  # type: ignore[no-untyped-def]
    def _make(role_id: int, *, with_role_row: bool = True) -> Account:
        auth_user_id = uuid4()
        user = add_user(auth_user_id=auth_user_id, role_id=role_id)
        if with_role_row and role_id == 2:
            db_session.add(Tutor(user_id=user.id, phone="0912345678"))
        if with_role_row and role_id == 3:
            db_session.add(Parent(user_id=user.id, phone="0987654321"))
        db_session.commit()
        return Account(user.id, {"Authorization": f"Bearer {make_token(auth_user_id)}"})

    return _make


@pytest.fixture
def tutor(make_account, subjects) -> Account:  # type: ignore[no-untyped-def]
    return make_account(2)


@pytest.fixture
def other_tutor(make_account, subjects) -> Account:  # type: ignore[no-untyped-def]
    return make_account(2)


@pytest.fixture
def create_profile(client: AsyncClient):  # type: ignore[no-untyped-def]
    async def _create(account: Account, **overrides: Any) -> dict[str, Any]:
        response = await client.post(
            "/api/tutor-profiles", json=valid_profile_payload(**overrides), headers=account.headers
        )
        assert response.status_code == 201, response.text
        return response.json()["data"]

    return _create


@pytest.fixture
def set_status(db_session: Session):  # type: ignore[no-untyped-def]

    def _set(profile_id: str, status: str, reject_reason: str | None = None) -> None:
        profile = db_session.get(TutorProfile, UUID(profile_id))
        assert profile is not None
        profile.status = status
        profile.reject_reason = reject_reason
        db_session.commit()

    return _set

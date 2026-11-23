import os
from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Engine, create_engine, make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.file_storage import get_file_storage
from app.core.security import SupabaseTokenVerifier, get_token_verifier
from app.db.base import Base
from app.db.models import Role, User
from app.db.session import get_db
from app.main import app
from tests.fakes import InMemoryFileStorage

pytest_plugins = ["tests.profile_fixtures"]

TEST_ISSUER = "https://test-project.supabase.co/auth/v1"
TEST_AUDIENCE = "authenticated"


@pytest.fixture
def private_key():  # type: ignore[no-untyped-def]
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def verifier(private_key) -> SupabaseTokenVerifier:  # type: ignore[no-untyped-def]
    settings = Settings(
        database_url="sqlite://",
        supabase_url="https://test-project.supabase.co",
        supabase_jwt_algorithms=["RS256"],
    )
    return SupabaseTokenVerifier(settings, key_resolver=lambda token: private_key.public_key())


def _test_engine() -> Engine:
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        return create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
    if "test" not in (make_url(url).database or ""):
        raise RuntimeError("TEST_DATABASE_URL phải trỏ tới database test riêng (tên chứa 'test').")
    return create_engine(url)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = _test_engine()
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        session.add_all(
            [
                Role(id=1, name="Quản trị viên"),
                Role(id=2, name="Sinh viên/Gia sư"),
                Role(id=3, name="Phụ huynh"),
            ]
        )
        session.commit()
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def storage() -> InMemoryFileStorage:
    return InMemoryFileStorage()


@pytest.fixture
async def client(
    db_session: Session, verifier: SupabaseTokenVerifier, storage: InMemoryFileStorage
) -> AsyncGenerator[AsyncClient, None]:
    def override_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            db_session.rollback()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_token_verifier] = lambda: verifier
    app.dependency_overrides[get_file_storage] = lambda: storage
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def add_user(db_session: Session):  # type: ignore[no-untyped-def]
    def _add_user(*, auth_user_id: UUID, is_active: bool = True, role_id: int = 2) -> User:
        user = User(
            id=uuid4(),
            auth_user_id=auth_user_id,
            role_id=role_id,
            full_name="Nguyễn Văn Gia Sư",
            login_identifier=f"{auth_user_id}@example.com",
            credential_reference=None,
            is_active=is_active,
            token_version=0,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(user)
        db_session.commit()
        return user

    return _add_user


@pytest.fixture
def make_token(private_key):  # type: ignore[no-untyped-def]
    def _make_token(
        subject: UUID,
        *,
        expires_in: timedelta = timedelta(minutes=30),
        signing_key=None,
    ) -> str:
        now = datetime.now(timezone.utc)
        return jwt.encode(
            {
                "sub": str(subject),
                "iss": TEST_ISSUER,
                "aud": TEST_AUDIENCE,
                "iat": now,
                "exp": now + expires_in,
                "role": "authenticated",
            },
            signing_key or private_key,
            algorithm="RS256",
            headers={"kid": "test-key"},
        )

    return _make_token

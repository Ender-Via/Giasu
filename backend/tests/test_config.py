import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_parse_csv_lists(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SUPABASE_JWT_ALGORITHMS", "ES256, RS256")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000, https://app.example.com")

    settings = Settings(_env_file=None)

    assert settings.supabase_jwt_algorithms == ["ES256", "RS256"]
    assert settings.cors_allowed_origins == [
        "http://localhost:3000",
        "https://app.example.com",
    ]


def test_settings_reject_legacy_hs256(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SUPABASE_JWT_ALGORITHMS", "HS256")

    with pytest.raises(ValidationError, match="ES256 hoặc RS256"):
        Settings(_env_file=None)

from functools import lru_cache
from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:54322/postgres"
    supabase_url: str = "http://localhost:54321"
    supabase_jwt_audience: str = "authenticated"
    supabase_jwt_algorithms: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["ES256", "RS256"]
    )
    cors_allowed_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )
    supabase_secret_key: SecretStr | None = None
    supabase_storage_bucket: str = "evidences"

    @field_validator("supabase_jwt_algorithms", "cors_allowed_origins", mode="before")
    @classmethod
    def split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("supabase_jwt_algorithms")
    @classmethod
    def allow_only_asymmetric_algorithms(cls, value: list[str]) -> list[str]:
        allowed = {"ES256", "RS256"}
        if not value or any(algorithm not in allowed for algorithm in value):
            raise ValueError("Chỉ hỗ trợ signing key Supabase ES256 hoặc RS256.")
        return value

    @property
    def supabase_issuer(self) -> str:
        return f"{self.supabase_url.rstrip('/')}/auth/v1"

    @property
    def supabase_jwks_url(self) -> str:
        return f"{self.supabase_issuer}/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()

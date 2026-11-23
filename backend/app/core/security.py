from collections.abc import Callable
from functools import lru_cache
from typing import Annotated, Any
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.core.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


class TokenVerificationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class SupabaseTokenVerifier:
    def __init__(
        self,
        settings: Settings,
        key_resolver: Callable[[str], Any] | None = None,
    ) -> None:
        self.settings = settings
        self._jwks_client = PyJWKClient(settings.supabase_jwks_url, cache_keys=True, lifespan=600)
        self._key_resolver = key_resolver or self._resolve_remote_key

    def _resolve_remote_key(self, token: str) -> Any:
        return self._jwks_client.get_signing_key_from_jwt(token).key

    def verify(self, token: str) -> UUID:
        try:
            signing_key = self._key_resolver(token)
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=self.settings.supabase_jwt_algorithms,
                audience=self.settings.supabase_jwt_audience,
                issuer=self.settings.supabase_issuer,
                options={"require": ["sub", "exp", "iss", "aud"]},
            )
            return UUID(claims["sub"])
        except jwt.ExpiredSignatureError as exc:
            raise TokenVerificationError(
                "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại."
            ) from exc
        except (jwt.PyJWTError, ValueError, TypeError) as exc:
            raise TokenVerificationError("Token không hợp lệ.") from exc


@lru_cache
def get_token_verifier() -> SupabaseTokenVerifier:
    return SupabaseTokenVerifier(get_settings())


def get_current_auth_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    verifier: Annotated[SupabaseTokenVerifier, Depends(get_token_verifier)],
) -> UUID:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bạn cần đăng nhập để tiếp tục.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return verifier.verify(credentials.credentials)
    except TokenVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

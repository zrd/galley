# src/app/security/auth.py
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str | None = Depends(api_key_header)) -> str:
    if api_key is None or api_key != settings.DEV_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key


def get_current_user_id(_: str = Depends(require_api_key)) -> UUID:
    return settings.DEV_USER_ID

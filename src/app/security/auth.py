"""
Authentication module with JWT token support.

Provides:
- Password hashing with bcrypt
- JWT token creation and validation
- FastAPI dependencies for protected routes
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

# JWT Bearer token security scheme
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(author_id: UUID, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token for an author.

    Args:
        author_id: The author's UUID
        expires_delta: Optional custom expiration time

    Returns:
        The encoded JWT token
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(UTC) + expires_delta
    payload = {
        "sub": str(author_id),
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(author_id: UUID, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT refresh token for an author.

    Args:
        author_id: The author's UUID
        expires_delta: Optional custom expiration time

    Returns:
        The encoded JWT token
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    expire = datetime.now(UTC) + expires_delta
    payload = {
        "sub": str(author_id),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT token string

    Returns:
        The decoded token payload

    Raises:
        HTTPException: If the token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_author_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> UUID:
    """
    FastAPI dependency to get the current authenticated author's ID.

    Extracts and validates the JWT token from the Authorization header.

    Args:
        credentials: The HTTP Authorization credentials

    Returns:
        The authenticated author's UUID

    Raises:
        HTTPException: If authentication fails
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        author_id = UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return author_id


def get_optional_author_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> UUID | None:
    """
    FastAPI dependency to optionally get the current author's ID.

    Unlike get_current_author_id, this does not raise an error if
    no authentication is provided. Useful for endpoints that have
    different behavior for authenticated vs anonymous users.

    Args:
        credentials: The HTTP Authorization credentials (optional)

    Returns:
        The author's UUID if authenticated, None otherwise
    """
    if credentials is None:
        return None

    try:
        return get_current_author_id(credentials)
    except HTTPException:
        return None


# Type aliases for cleaner route signatures
CurrentAuthorId = Annotated[UUID, Depends(get_current_author_id)]
OptionalAuthorId = Annotated[UUID | None, Depends(get_optional_author_id)]

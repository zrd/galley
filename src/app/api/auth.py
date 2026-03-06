"""
Authentication endpoints for user registration, login, and token refresh.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import SQLAlchemyAuthorRepository
from app.schemas import AuthorCreate, AuthorRead, LoginRequest, RefreshRequest, TokenResponse
from app.security.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.services import AuthorService

router = APIRouter()


def get_author_service(db: Annotated[Session, Depends(get_db)]) -> AuthorService:
    """Dependency to get an AuthorService with database session."""
    repo = SQLAlchemyAuthorRepository(db)
    return AuthorService(repo)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    author_in: AuthorCreate,
    service: Annotated[AuthorService, Depends(get_author_service)],
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """
    Register a new author account.

    Returns access and refresh tokens on successful registration.
    """
    # Check if email already exists
    existing = service.get_by_email(author_in.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create author
    password_hash = hash_password(author_in.password)
    author = service.create(
        email=author_in.email,
        password_hash=password_hash,
        display_name=author_in.display_name,
    )
    # Generate tokens
    access_token = create_access_token(author.id)
    refresh_token = create_refresh_token(author.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=TokenResponse)
def login(
    login_in: LoginRequest,
    service: Annotated[AuthorService, Depends(get_author_service)],
) -> TokenResponse:
    """
    Login with email and password.

    Returns access and refresh tokens on successful login.
    """
    author = service.get_by_email(login_in.email)
    if author is None or not verify_password(login_in.password, author.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(author.id)
    refresh_token = create_refresh_token(author.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    refresh_in: RefreshRequest,
    service: Annotated[AuthorService, Depends(get_author_service)],
) -> TokenResponse:
    """
    Refresh an access token using a refresh token.

    Returns new access and refresh tokens.
    """
    payload = decode_token(refresh_in.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    try:
        author_id = UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Verify author still exists
    try:
        service.get(author_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Author not found",
        )

    access_token = create_access_token(author_id)
    new_refresh_token = create_refresh_token(author_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )

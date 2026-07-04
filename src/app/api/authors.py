"""
Author profile endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import AuthorRepository
from app.schemas import AuthorRead, AuthorUpdate
from app.security.auth import CurrentAuthorId
from app.services import AuthorService

router = APIRouter()


def get_author_service(db: Annotated[Session, Depends(get_db)]) -> AuthorService:
    """Dependency to get an AuthorService with database session."""
    repo = AuthorRepository(db)
    return AuthorService(repo)


@router.get("/me", response_model=AuthorRead)
def get_current_author(
    author_id: CurrentAuthorId,
    service: Annotated[AuthorService, Depends(get_author_service)],
) -> AuthorRead:
    """Get the current authenticated author's profile."""
    author = service.get(author_id)
    return AuthorRead.model_validate(author)


@router.put("/me", response_model=AuthorRead)
def update_current_author(
    author_id: CurrentAuthorId,
    update_in: AuthorUpdate,
    service: Annotated[AuthorService, Depends(get_author_service)],
) -> AuthorRead:
    """Update the current authenticated author's profile."""
    author = service.get(author_id)
    author = service.update(author, update_in)
    return AuthorRead.model_validate(author)

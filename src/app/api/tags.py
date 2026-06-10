"""
Tag endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import SQLAlchemyTagRepository
from app.schemas import TagRead
from app.security.auth import CurrentAuthorId
from app.services import TagService

router = APIRouter()


def get_tag_service(db: Annotated[Session, Depends(get_db)]) -> TagService:
    """Dependency to get a TagService with database session."""
    tag_repo = SQLAlchemyTagRepository(db)
    return TagService(tag_repo)


@router.get("/", response_model=list[TagRead])
def list_tags(
    service: Annotated[TagService, Depends(get_tag_service)],
    owner_id: CurrentAuthorId
) -> list[TagRead]:
    tags = service.list_all(owner_id=owner_id)
    return [TagRead.model_validate(t) for t in tags]


@router.get("/{slug}", response_model=TagRead)
def get_tag(
    service: Annotated[TagService, Depends(get_tag_service)],
    slug: str,
    owner_id: CurrentAuthorId,
) -> TagRead:
    tag = service.get_by_slug(slug=slug, owner_id=owner_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    return TagRead.model_validate(tag)

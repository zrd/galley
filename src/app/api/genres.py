"""
Genre endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain import GenreNotFound
from app.repositories import SQLAlchemyGenreRepository
from app.schemas import GenreListItem, GenreRead, GenreTree
from app.services import GenreService

router = APIRouter()


def get_genre_service(db: Annotated[Session, Depends(get_db)]) -> GenreService:
    """Dependency to get a GenreService with database session."""
    genre_repo = SQLAlchemyGenreRepository(db)
    return GenreService(genre_repo)


@router.post("/", response_model=GenreRead, status_code=status.HTTP_201_CREATED)
def create_genre(
    service: Annotated[GenreService, Depends(get_genre_service)],
    name: Annotated[str, Form(min_length=1)],
    description: Annotated[str | None, Form()] = None,
    parent_id: Annotated[int | None, Form()] = None,
) -> GenreRead:
    genre = service.create(name=name, description=description, parent_id=parent_id)
    return GenreRead.model_validate(genre)


@router.get("/", response_model=list[GenreListItem])
def list_genres(
    service: Annotated[GenreService, Depends(get_genre_service)]
) -> list[GenreListItem]:
    return [GenreListItem.model_validate(g) for g in service.list_all()]


@router.get("/tree", response_model=list[GenreTree])
def get_tree(
    service: Annotated[GenreService, Depends(get_genre_service)]
) -> list[GenreTree]:
    return service.get_tree()


@router.get("/{genre_id}", response_model=GenreRead)
def get_genre(
    genre_id: int,
    service: Annotated[GenreService, Depends(get_genre_service)]
) -> GenreRead:
    try:
        genre = service.get(genre_id)
    except GenreNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Genre not found")
    return GenreRead.model_validate(genre)


@router.get("/{genre_id}/children", response_model=list[GenreListItem])
def list_by_parent(
    genre_id: int,
    service: Annotated[GenreService, Depends(get_genre_service)]
) -> list[GenreListItem]:
    return [GenreListItem.model_validate(g) for g in service.list_by_parent(parent_id=genre_id)]

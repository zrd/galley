"""
Customer facing store endpoints
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain import (
    AuthorNotFound,
    EbookNotFound,
    ManuscriptNotFound,
    UnlistedDownloadLimitExceeded,
)
from app.repositories import StoreRepository
from app.schemas import (
    StoreAuthorDetail,
    StoreAuthorListItem,
    StoreBrowseItem,
    StoreEditionDetail,
    StoreGenreTree,
    StoreManuscriptDetail,
    StorePaginatedResponse,
)
from app.services import StoreService

router = APIRouter()

def get_store_service(db: Annotated[Session, Depends(get_db)]) -> StoreService:
    repo = StoreRepository(db)
    return StoreService(repo)


@router.get("/ebooks", response_model=StorePaginatedResponse[StoreBrowseItem])
def list_ebooks(
        service: Annotated[StoreService, Depends(get_store_service)],
        page: Annotated[int, Query(ge=1)] = 1,
        per_page: Annotated[int, Query(ge=1, le=50)] = 20,
        author_ids: Annotated[list[UUID] | None, Query()] = None,
        genre_slugs: Annotated[list[str] | None, Query(alias="genre")] = None,
        tag_slugs: Annotated[list[str] | None, Query(alias="tag")] = None,
        min_price: Annotated[int | None, Query(ge=0)] = None,
        max_price: Annotated[int | None, Query(ge=0)] = None,
        search_term: Annotated[str | None, Query(alias="q")] = None,
        sorting_method: Annotated[str, Query(alias="sort")] = "newest",
) -> StorePaginatedResponse[StoreBrowseItem]:
    results, total = service.browse_listings(
        page=page,
        per_page=per_page,
        author_ids=author_ids,
        genre_slugs=genre_slugs,
        tag_slugs=tag_slugs,
        min_price=min_price,
        max_price=max_price,
        search_term=search_term,
        sorting_method=sorting_method,
    )
    return StorePaginatedResponse(
        items=[StoreBrowseItem.model_validate(r) for r in results],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/ebooks/{manuscript_id}", response_model=StoreManuscriptDetail)
def lookup_listing(
        service: Annotated[StoreService, Depends(get_store_service)],
        manuscript_id: UUID,
) -> StoreManuscriptDetail:
    try:
        m = service.get_listing(manuscript_id)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    return StoreManuscriptDetail.model_validate(m)


@router.get("/editions/{ebook_id}", response_model=StoreEditionDetail)
def lookup_edition(
        service: Annotated[StoreService, Depends(get_store_service)],
        ebook_id: UUID,
) -> StoreEditionDetail:
    try:
        e = service.get_edition(ebook_id)
    except EbookNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Edition not found")
    except UnlistedDownloadLimitExceeded:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Edition not available")

    return StoreEditionDetail.model_validate(e)


@router.get("/authors", response_model=StorePaginatedResponse[StoreAuthorListItem])
def browse_authors(
        service: Annotated[StoreService, Depends(get_store_service)],
        page: Annotated[int, Query(ge=1)] = 1,
        per_page: Annotated[int, Query(ge=1, le=50)] = 20,
) -> StorePaginatedResponse[StoreAuthorListItem]:
    results, total = service.list_author_profiles(page=page, per_page=per_page)
    return StorePaginatedResponse(
        items=[StoreAuthorListItem.model_validate(r) for r in results],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/authors/{author_id}", response_model=StoreAuthorDetail)
def lookup_author(
        service: Annotated[StoreService, Depends(get_store_service)],
        author_id: UUID,
) -> StoreAuthorDetail:
    try:
        a = service.get_author_profile(author_id)
    except AuthorNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Author not found")

    return StoreAuthorDetail.model_validate(a)


@router.get("/genres", response_model=list[StoreGenreTree])
def browse_genres(
        service: Annotated[StoreService, Depends(get_store_service)],
) -> list[StoreGenreTree]:
    return service.list_genres_with_counts()

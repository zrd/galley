"""
Sample definition endpoints.

Samples define how to create promotional excerpts from manuscripts.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain import ManuscriptNotFound, SampleNotFound
from app.repositories import (
    SQLAlchemyEbookRepository,
    SQLAlchemyManuscriptRepository,
    SQLAlchemySampleRepository,
)
from app.schemas import EbookGenerateRequest, EbookRead, SampleCreate, SampleRead, SampleUpdate
from app.security.auth import CurrentAuthorId
from app.services import (
    EbookService,
    GenerationError,
    GenerationService,
    ManuscriptService,
    SampleService,
)

router = APIRouter()


def get_manuscript_service(db: Annotated[Session, Depends(get_db)]) -> ManuscriptService:
    manuscript_repo = SQLAlchemyManuscriptRepository(db)
    sample_repo = SQLAlchemySampleRepository(db)
    ebook_repo = SQLAlchemyEbookRepository(db)
    return ManuscriptService(manuscript_repo, sample_repo, ebook_repo)


def get_sample_service(db: Annotated[Session, Depends(get_db)]) -> SampleService:
    repo = SQLAlchemySampleRepository(db)
    ebook_repo = SQLAlchemyEbookRepository(db)
    return SampleService(repo, ebook_repo)


def get_ebook_service(db: Annotated[Session, Depends(get_db)]) -> EbookService:
    repo = SQLAlchemyEbookRepository(db)
    return EbookService(repo)


def get_generation_service(db: Annotated[Session, Depends(get_db)]) -> GenerationService:
    ebook_repo = SQLAlchemyEbookRepository(db)
    return GenerationService(ebook_repo)


@router.post(
    "/manuscripts/{manuscript_id}/samples",
    response_model=SampleRead,
    status_code=status.HTTP_201_CREATED,
)
def create_sample(
    manuscript_id: str,
    sample_in: SampleCreate,
    author_id: CurrentAuthorId,
    manuscript_service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    sample_service: Annotated[SampleService, Depends(get_sample_service)],
    db: Annotated[Session, Depends(get_db)],
) -> SampleRead:
    """Create a new sample definition for a manuscript."""
    try:
        mid = UUID(manuscript_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    # Verify manuscript ownership
    if not manuscript_service.check_ownership(mid, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    sample = sample_service.create(
        manuscript_id=mid,
        title=sample_in.title,
        excerpt_start=sample_in.excerpt_start,
        excerpt_end=sample_in.excerpt_end,
        promo_header=sample_in.promo_header,
        promo_footer=sample_in.promo_footer,
    )
    return SampleRead(
        id=sample.id,
        manuscript_id=sample.manuscript_id,
        title=sample.title,
        excerpt_start=sample.excerpt_start,
        excerpt_end=sample.excerpt_end,
        promo_header=sample.promo_header,
        promo_footer=sample.promo_footer,
        created_at=sample.created_at,
        updated_at=sample.updated_at,
    )


@router.get("/manuscripts/{manuscript_id}/samples", response_model=list[SampleRead])
def list_samples(
    manuscript_id: str,
    author_id: CurrentAuthorId,
    manuscript_service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    sample_service: Annotated[SampleService, Depends(get_sample_service)],
    include_deleted: Annotated[bool, Query()] = False,
) -> list[SampleRead]:
    """List all samples for a manuscript."""
    try:
        mid = UUID(manuscript_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    if not manuscript_service.check_ownership(mid, author_id, include_deleted=include_deleted):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    samples = sample_service.list_by_manuscript(mid, include_deleted=include_deleted)
    return [
        SampleRead(
            id=s.id,
            manuscript_id=s.manuscript_id,
            title=s.title,
            excerpt_start=s.excerpt_start,
            excerpt_end=s.excerpt_end,
            promo_header=s.promo_header,
            promo_footer=s.promo_footer,
            created_at=s.created_at,
            updated_at=s.updated_at,
            deleted_at=s.deleted_at,
        )
        for s in samples
    ]


@router.get("/{sample_id}", response_model=SampleRead)
def get_sample(
    sample_id: str,
    author_id: CurrentAuthorId,
    manuscript_service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    sample_service: Annotated[SampleService, Depends(get_sample_service)],
) -> SampleRead:
    """Get a specific sample definition."""
    try:
        sid = UUID(sample_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")

    try:
        sample = sample_service.get(sid)
    except SampleNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")

    # Verify ownership through manuscript
    if not manuscript_service.check_ownership(sample.manuscript_id, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")

    return SampleRead(
        id=sample.id,
        manuscript_id=sample.manuscript_id,
        title=sample.title,
        excerpt_start=sample.excerpt_start,
        excerpt_end=sample.excerpt_end,
        promo_header=sample.promo_header,
        promo_footer=sample.promo_footer,
        created_at=sample.created_at,
        updated_at=sample.updated_at,
    )


@router.put("/{sample_id}", response_model=SampleRead)
def update_sample(
    sample_id: str,
    update_in: SampleUpdate,
    author_id: CurrentAuthorId,
    manuscript_service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    sample_service: Annotated[SampleService, Depends(get_sample_service)],
    db: Annotated[Session, Depends(get_db)],
) -> SampleRead:
    """Update a sample definition."""
    try:
        sid = UUID(sample_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")

    try:
        sample = sample_service.get(sid)
    except SampleNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")

    if not manuscript_service.check_ownership(sample.manuscript_id, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")

    sample = sample_service.update(
        sid,
        title=update_in.title,
        excerpt_start=update_in.excerpt_start,
        excerpt_end=update_in.excerpt_end,
        promo_header=update_in.promo_header,
        promo_footer=update_in.promo_footer,
    )
    return SampleRead(
        id=sample.id,
        manuscript_id=sample.manuscript_id,
        title=sample.title,
        excerpt_start=sample.excerpt_start,
        excerpt_end=sample.excerpt_end,
        promo_header=sample.promo_header,
        promo_footer=sample.promo_footer,
        created_at=sample.created_at,
        updated_at=sample.updated_at,
    )


@router.delete("/{sample_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sample(
    sample_id: str,
    author_id: CurrentAuthorId,
    manuscript_service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    sample_service: Annotated[SampleService, Depends(get_sample_service)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Soft delete a sample definition and its generated ebooks."""
    try:
        sid = UUID(sample_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")

    try:
        sample = sample_service.get(sid)
    except SampleNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")

    if not manuscript_service.check_ownership(sample.manuscript_id, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")

    sample_service.soft_delete(sid)


@router.post("/{sample_id}/restore", response_model=SampleRead)
def restore_sample(
    sample_id: str,
    author_id: CurrentAuthorId,
    manuscript_service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    sample_service: Annotated[SampleService, Depends(get_sample_service)],
    db: Annotated[Session, Depends(get_db)],
) -> SampleRead:
    """Restore a soft-deleted sample and its generated ebooks."""
    try:
        sid = UUID(sample_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")

    try:
        sample = sample_service.get(sid, include_deleted=True)
    except SampleNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")

    if not manuscript_service.check_ownership(sample.manuscript_id, author_id, include_deleted=True):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")

    sample_service.restore(sid)
    sample = sample_service.get(sid)
    return SampleRead(
        id=sample.id,
        manuscript_id=sample.manuscript_id,
        title=sample.title,
        excerpt_start=sample.excerpt_start,
        excerpt_end=sample.excerpt_end,
        promo_header=sample.promo_header,
        promo_footer=sample.promo_footer,
        created_at=sample.created_at,
        updated_at=sample.updated_at,
    )


@router.post("/{sample_id}/generate", response_model=list[EbookRead])
async def generate_sample_ebooks(
    sample_id: str,
    generate_in: EbookGenerateRequest,
    author_id: CurrentAuthorId,
    manuscript_service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    sample_service: Annotated[SampleService, Depends(get_sample_service)],
    generation_service: Annotated[GenerationService, Depends(get_generation_service)],
    db: Annotated[Session, Depends(get_db)],
) -> list[EbookRead]:
    """Generate sample ebooks in the requested formats."""
    try:
        sid = UUID(sample_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")

    try:
        sample = sample_service.get(sid)
    except SampleNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")

    if not manuscript_service.check_ownership(sample.manuscript_id, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")

    try:
        manuscript = manuscript_service.get(sample.manuscript_id)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    ebooks = []
    for output_format in generate_in.output_formats:
        try:
            ebook = await generation_service.generate_sample_ebook(
                manuscript=manuscript,
                sample=sample,
                output_format=output_format,
            )
            ebooks.append(ebook)
        except GenerationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return [
        EbookRead(
            id=e.id,
            manuscript_id=e.manuscript_id,
            sample_id=e.sample_id,
            output_format=e.output_format,
            file_size_bytes=e.file_size_bytes,
            download_count=e.download_count,
            created_at=e.created_at,
        )
        for e in ebooks
    ]

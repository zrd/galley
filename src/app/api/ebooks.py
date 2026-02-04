"""
Ebook management and download endpoints.
"""

import hashlib
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain import Download, EbookNotFound, ManuscriptNotFound
from app.repositories import (
    SQLAlchemyDownloadRepository,
    SQLAlchemyEbookRepository,
    SQLAlchemyManuscriptRepository,
    SQLAlchemySampleRepository,
)
from app.schemas import EbookGenerateRequest, EbookListItem, EbookRead
from app.security.auth import CurrentAuthorId, OptionalAuthorId
from app.services import EbookService, GenerationError, GenerationService, ManuscriptService
from app.storage import get_content_type_for_format, get_storage_backend

router = APIRouter()


def get_manuscript_service(db: Annotated[Session, Depends(get_db)]) -> ManuscriptService:
    manuscript_repo = SQLAlchemyManuscriptRepository(db)
    sample_repo = SQLAlchemySampleRepository(db)
    ebook_repo = SQLAlchemyEbookRepository(db)
    return ManuscriptService(manuscript_repo, sample_repo, ebook_repo)


def get_ebook_service(db: Annotated[Session, Depends(get_db)]) -> EbookService:
    repo = SQLAlchemyEbookRepository(db)
    return EbookService(repo)


def get_generation_service(db: Annotated[Session, Depends(get_db)]) -> GenerationService:
    ebook_repo = SQLAlchemyEbookRepository(db)
    return GenerationService(ebook_repo)


def get_download_repo(db: Annotated[Session, Depends(get_db)]) -> SQLAlchemyDownloadRepository:
    return SQLAlchemyDownloadRepository(db)


@router.get("/", response_model=list[EbookListItem])
def list_ebooks(
    author_id: CurrentAuthorId,
    ebook_service: Annotated[EbookService, Depends(get_ebook_service)],
    include_deleted: Annotated[bool, Query()] = False,
) -> list[EbookListItem]:
    """List all ebooks for the current author."""
    ebooks = ebook_service.list_by_author(author_id, include_deleted=include_deleted)
    return [
        EbookListItem(
            id=e.id,
            manuscript_id=e.manuscript_id,
            sample_id=e.sample_id,
            output_format=e.output_format,
            file_size_bytes=e.file_size_bytes,
            download_count=e.download_count,
            created_at=e.created_at,
            deleted_at=e.deleted_at,
        )
        for e in ebooks
    ]


@router.get("/{ebook_id}", response_model=EbookRead)
def get_ebook(
    ebook_id: str,
    author_id: CurrentAuthorId,
    manuscript_service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    ebook_service: Annotated[EbookService, Depends(get_ebook_service)],
) -> EbookRead:
    """Get ebook metadata."""
    try:
        eid = UUID(ebook_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    try:
        ebook = ebook_service.get(eid)
    except EbookNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    # Verify ownership through manuscript
    if not manuscript_service.check_ownership(ebook.manuscript_id, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    return EbookRead(
        id=ebook.id,
        manuscript_id=ebook.manuscript_id,
        sample_id=ebook.sample_id,
        output_format=ebook.output_format,
        file_size_bytes=ebook.file_size_bytes,
        download_count=ebook.download_count,
        created_at=ebook.created_at,
    )


@router.get("/{ebook_id}/download")
async def download_ebook(
    ebook_id: str,
    request: Request,
    ebook_service: Annotated[EbookService, Depends(get_ebook_service)],
    download_repo: Annotated[SQLAlchemyDownloadRepository, Depends(get_download_repo)],
    db: Annotated[Session, Depends(get_db)],
    tracking_code: Annotated[str | None, Query(alias="t")] = None,
) -> Response:
    """
    Download an ebook file.

    This endpoint is public and does not require authentication.
    Downloads are tracked for analytics.

    Query parameters:
    - t: Optional tracking code for QR/link attribution
    """
    try:
        eid = UUID(ebook_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    try:
        ebook = ebook_service.get(eid)
    except EbookNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    # Download file from storage
    storage = get_storage_backend()
    try:
        file_data = await storage.download(ebook.file_key)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ebook file not found"
        )

    # Record download
    client_ip = request.client.host if request.client else None
    ip_hash = None
    if client_ip:
        # Hash IP for privacy
        ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:32]

    download = Download(
        ebook_id=ebook.id,
        ip_hash=ip_hash,
        tracking_code=tracking_code,
    )
    download_repo.add(download)

    # Increment download count
    ebook_service.increment_download(ebook.id)
    db.commit()

    # Return file
    content_type = get_content_type_for_format(ebook.output_format.value)
    filename = f"ebook.{ebook.output_format.value}"

    return Response(
        content=file_data,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(file_data)),
        },
    )


@router.delete("/{ebook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ebook(
    ebook_id: str,
    author_id: CurrentAuthorId,
    manuscript_service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    ebook_service: Annotated[EbookService, Depends(get_ebook_service)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Soft delete an ebook. Files are retained for potential restoration."""
    try:
        eid = UUID(ebook_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    try:
        ebook = ebook_service.get(eid)
    except EbookNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    if not manuscript_service.check_ownership(ebook.manuscript_id, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    ebook_service.soft_delete(eid)
    db.commit()


@router.post("/{ebook_id}/restore", response_model=EbookRead)
def restore_ebook(
    ebook_id: str,
    author_id: CurrentAuthorId,
    manuscript_service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    ebook_service: Annotated[EbookService, Depends(get_ebook_service)],
    db: Annotated[Session, Depends(get_db)],
) -> EbookRead:
    """Restore a soft-deleted ebook."""
    try:
        eid = UUID(ebook_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    try:
        ebook = ebook_service.get(eid, include_deleted=True)
    except EbookNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    if not manuscript_service.check_ownership(ebook.manuscript_id, author_id, include_deleted=True):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    ebook_service.restore(eid)
    db.commit()

    ebook = ebook_service.get(eid)
    return EbookRead(
        id=ebook.id,
        manuscript_id=ebook.manuscript_id,
        sample_id=ebook.sample_id,
        output_format=ebook.output_format,
        file_size_bytes=ebook.file_size_bytes,
        download_count=ebook.download_count,
        created_at=ebook.created_at,
    )


# Ebook generation endpoint (on manuscript)
@router.post("/manuscripts/{manuscript_id}/generate", response_model=list[EbookRead])
async def generate_ebooks(
    manuscript_id: str,
    generate_in: EbookGenerateRequest,
    author_id: CurrentAuthorId,
    manuscript_service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    generation_service: Annotated[GenerationService, Depends(get_generation_service)],
    db: Annotated[Session, Depends(get_db)],
) -> list[EbookRead]:
    """
    Generate ebooks from a manuscript in the requested formats.

    The manuscript must be in READY state.
    """
    try:
        mid = UUID(manuscript_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    if not manuscript_service.check_ownership(mid, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    try:
        manuscript = manuscript_service.get(mid)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    ebooks = []
    for output_format in generate_in.output_formats:
        try:
            ebook = await generation_service.generate_full_ebook(
                manuscript=manuscript,
                output_format=output_format,
            )
            ebooks.append(ebook)
        except GenerationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    db.commit()

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

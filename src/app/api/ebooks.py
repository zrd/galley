"""
Ebook management and download endpoints.
"""

import hashlib
import unicodedata
from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain import Download, Ebook, EbookNotFound, ManuscriptInDraft, ManuscriptNotFound
from app.repositories import (
    AuthorRepository,
    DownloadRepository,
    EbookRepository,
    ManuscriptRepository,
    SampleRepository,
)
from app.schemas import EbookGenerateRequest, EbookListItem, EbookRead
from app.schemas.ebook import EbookUpdate
from app.security.auth import CurrentAuthorId
from app.services import (
    AuthorService,
    EbookService,
    GenerationError,
    GenerationService,
    ManuscriptService,
)
from app.storage import get_content_type_for_format, get_storage_backend

router = APIRouter()


def _ascii_filename(name: str) -> str:
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").strip()


def get_manuscript_service(db: Annotated[Session, Depends(get_db)]) -> ManuscriptService:
    manuscript_repo = ManuscriptRepository(db)
    sample_repo = SampleRepository(db)
    ebook_repo = EbookRepository(db)
    return ManuscriptService(manuscript_repo, sample_repo, ebook_repo)


def get_ebook_service(db: Annotated[Session, Depends(get_db)]) -> EbookService:
    manuscript_repo = ManuscriptRepository(db)
    repo = EbookRepository(db)
    return EbookService(repo, manuscript_repo)


def get_generation_service(db: Annotated[Session, Depends(get_db)]) -> GenerationService:
    ebook_repo = EbookRepository(db)
    return GenerationService(ebook_repo)


def get_download_repo(db: Annotated[Session, Depends(get_db)]) -> DownloadRepository:
    return DownloadRepository(db)


def get_author_service(db: Annotated[Session, Depends(get_db)]) -> AuthorService:
    repo = AuthorRepository(db)
    return AuthorService(repo)


@router.get("/", response_model=list[EbookListItem])
def list_ebooks(
    author_id: CurrentAuthorId,
    ebook_service: Annotated[EbookService, Depends(get_ebook_service)],
    include_deleted: Annotated[bool, Query()] = False,
) -> list[EbookListItem]:
    """List all ebooks for the current author."""
    ebooks = ebook_service.list_by_author(author_id, include_deleted=include_deleted)
    return [EbookListItem.model_validate(e) for e in ebooks]


@router.get("/{ebook_id}", response_model=EbookRead)
def get_ebook(
    ebook_id: UUID,
    author_id: CurrentAuthorId,
    manuscript_service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    ebook_service: Annotated[EbookService, Depends(get_ebook_service)],
) -> EbookRead:
    """Get ebook metadata."""
    try:
        ebook = ebook_service.get(ebook_id)
    except EbookNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    # Verify ownership through manuscript
    if not manuscript_service.check_ownership(ebook.manuscript_id, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    return EbookRead.model_validate(ebook)


@router.get("/{ebook_id}/download")
async def download_ebook(
    ebook_id: UUID,
    request: Request,
    ebook_service: Annotated[EbookService, Depends(get_ebook_service)],
    download_repo: Annotated[DownloadRepository, Depends(get_download_repo)],
    tracking_code: Annotated[str | None, Query(alias="t")] = None,
) -> FileResponse:
    """
    Download an ebook file.

    This endpoint is public and does not require authentication.
    Downloads are tracked for analytics.

    Query parameters:
    - t: Optional tracking code for QR/link attribution
    """
    try:
        ebook = ebook_service.get_public_download(ebook_id)
    except EbookNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")
    except ManuscriptInDraft:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Temporarily unavailable")

    storage = get_storage_backend()
    try:
        asset_path = await storage.get_url(ebook.file_key)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook file not found")

    media_type = get_content_type_for_format(ebook.output_format.value)
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
    ebook_service.increment_download(ebook.id)
    return FileResponse(
        asset_path,
        media_type=media_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="{_ascii_filename(ebook.download_filename)}"; '
                f"filename*=UTF-8''{quote(ebook.download_filename)}"
            )
        }
    )


@router.delete("/{ebook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ebook(
    ebook_id: UUID,
    author_id: CurrentAuthorId,
    manuscript_service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    ebook_service: Annotated[EbookService, Depends(get_ebook_service)],
) -> None:
    """Soft delete an ebook. Files are retained for potential restoration."""
    try:
        ebook = ebook_service.get(ebook_id)
    except EbookNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    if not manuscript_service.check_ownership(ebook.manuscript_id, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    ebook_service.soft_delete(ebook_id)


@router.post("/{ebook_id}/restore", response_model=EbookRead)
def restore_ebook(
    ebook_id: UUID,
    author_id: CurrentAuthorId,
    manuscript_service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    ebook_service: Annotated[EbookService, Depends(get_ebook_service)],
) -> EbookRead:
    """Restore a soft-deleted ebook."""
    try:
        ebook = ebook_service.get(ebook_id, include_deleted=True)
    except EbookNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    if not manuscript_service.check_ownership(ebook.manuscript_id, author_id, include_deleted=True):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    ebook_service.restore(ebook_id)
    ebook = ebook_service.get(ebook_id)
    return EbookRead.model_validate(ebook)


# Ebook generation endpoint (on manuscript)
@router.post("/manuscripts/{manuscript_id}/generate", response_model=list[EbookRead])
async def generate_ebooks(
    manuscript_id: UUID,
    generate_in: EbookGenerateRequest,
    author_id: CurrentAuthorId,
    manuscript_service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    generation_service: Annotated[GenerationService, Depends(get_generation_service)],
    author_service: Annotated[AuthorService, Depends(get_author_service)],
) -> list[EbookRead]:
    """
    Generate ebooks from a manuscript in the requested formats.

    The manuscript must be in READY state.
    """
    if not manuscript_service.check_ownership(manuscript_id, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    try:
        manuscript = manuscript_service.get(manuscript_id)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    if not manuscript.can_generate_ebook():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Manuscript must be in READY state to generate ebooks (current: {manuscript.state.value})",
        )

    # Get author for display name in filename
    author = author_service.get(author_id)

    ebooks = []
    for output_format in generate_in.output_formats:
        try:
            ebook = await generation_service.generate_full_ebook(
                manuscript=manuscript,
                output_format=output_format,
                author_display_name=author.display_name,
            )
            ebooks.append(ebook)
        except GenerationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not generate {output_format.value.upper()} from this manuscript. The source format may not support this conversion.",
            )

    return [EbookRead.model_validate(e) for e in ebooks]


@router.patch("/{ebook_id}", response_model=EbookRead)
def update_ebook_price(
    ebook_id: UUID,
    update_in: EbookUpdate,
    author_id: CurrentAuthorId,
    manuscript_service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    ebook_service: Annotated[EbookService, Depends(get_ebook_service)],
) -> EbookRead:
    try:
        ebook = ebook_service.get(ebook_id, include_deleted=False)
    except EbookNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    if not manuscript_service.check_ownership(ebook.manuscript_id, author_id, include_deleted=False):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    ebook_service.update_price(ebook=ebook, update_in=update_in)
    ebook = ebook_service.get(ebook_id)
    return EbookRead.model_validate(ebook)


def get_owned_ebook(
    ebook_id: UUID,
    author_id: CurrentAuthorId,
    ebook_service: Annotated[EbookService, Depends(get_ebook_service)],
    manuscript_service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
) -> Ebook:
    try:
        ebook = ebook_service.get(ebook_id, include_deleted=False)
    except EbookNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    if not manuscript_service.check_ownership(ebook.manuscript_id, author_id, include_deleted=True):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ebook not found")

    return ebook


@router.post("/{ebook_id}/publish", response_model=EbookRead)
def publish_ebook(
    ebook: Annotated[Ebook, Depends(get_owned_ebook)],
    ebook_service: Annotated[EbookService, Depends(get_ebook_service)],
) -> EbookRead:
    ebook = ebook_service.publish(ebook_id=ebook.id)
    return EbookRead.model_validate(ebook)


@router.post("/{ebook_id}/unlist", response_model=EbookRead)
def unlist_ebook(
    ebook: Annotated[Ebook, Depends(get_owned_ebook)],
    ebook_service: Annotated[EbookService, Depends(get_ebook_service)],
) -> EbookRead:
    ebook = ebook_service.unlist(ebook_id=ebook.id)
    return EbookRead.model_validate(ebook)


@router.post("/{ebook_id}/make-private", response_model=EbookRead)
def make_ebook_private(
    ebook: Annotated[Ebook, Depends(get_owned_ebook)],
    ebook_service: Annotated[EbookService, Depends(get_ebook_service)],
) -> EbookRead:
    ebook = ebook_service.make_private(ebook_id=ebook.id)
    return EbookRead.model_validate(ebook)

"""
Manuscript management endpoints.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain import InvalidStateTransition, ManuscriptNotFound, SourceFormat
from app.repositories import (
    EbookRepository,
    ManuscriptRepository,
    SampleRepository,
    TagRepository,
)
from app.schemas import ManuscriptListItem, ManuscriptRead, ManuscriptUpdate
from app.security.auth import CurrentAuthorId
from app.services import ManuscriptService
from app.storage import get_content_type_for_format, get_storage_backend

router = APIRouter()


def get_manuscript_service(db: Annotated[Session, Depends(get_db)]) -> ManuscriptService:
    """Dependency to get a ManuscriptService with database session."""
    manuscript_repo = ManuscriptRepository(db)
    sample_repo = SampleRepository(db)
    ebook_repo = EbookRepository(db)
    tag_repo = TagRepository(db)
    return ManuscriptService(manuscript_repo, sample_repo, ebook_repo, tag_repo)


@router.post("/", response_model=ManuscriptRead, status_code=status.HTTP_201_CREATED)
async def create_manuscript(
    author_id: CurrentAuthorId,
    title: Annotated[str, Form(min_length=1)],
    source_format: Annotated[SourceFormat, Form()],
    file: Annotated[UploadFile, File()],
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    description: Annotated[str | None, Form()] = None,
    genre_ids: list[int] = Form(default=[]),
    tag_names: list[str] = Form(default=[]),
) -> ManuscriptRead:
    """
    Upload a new manuscript.

    The manuscript file should be in one of the supported formats:
    - EPUB (.epub)
    - PDF (.pdf)
    - DOCX (.docx)
    - ODT (.odt)
    """
    # Validate title is not whitespace only
    if not title.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=[{"loc": ["body", "title"], "msg": "title cannot be whitespace only", "type": "value_error"}],
        )

    # Read file contents
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )

    filename = file.filename or f"manuscript.{source_format.value}"
    manuscript = await service.create(
        author_id=author_id,
        title=title,
        source_format=source_format,
        filename=filename,
        content=content,
        description=description,
        genre_ids=genre_ids,
        tag_names=tag_names,
    )
    return ManuscriptRead.model_validate(manuscript)


@router.get("/", response_model=list[ManuscriptListItem])
def list_manuscripts(
    author_id: CurrentAuthorId,
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    include_deleted: Annotated[bool, Query()] = False,
) -> list[ManuscriptListItem]:
    """List all manuscripts for the current author."""
    manuscripts = service.list_by_author(author_id, include_deleted=include_deleted)
    return [ManuscriptListItem.model_validate(m) for m in manuscripts]


@router.get("/{manuscript_id}", response_model=ManuscriptRead)
def get_manuscript(
    manuscript_id: UUID,
    author_id: CurrentAuthorId,
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
) -> ManuscriptRead:
    """Get a specific manuscript by ID."""
    try:
        manuscript = service.get(manuscript_id)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    if manuscript.author_id != author_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    return ManuscriptRead.model_validate(manuscript)


@router.put("/{manuscript_id}", response_model=ManuscriptRead)
def update_manuscript(
    manuscript_id: UUID,
    update_in: ManuscriptUpdate,
    author_id: CurrentAuthorId,
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
) -> ManuscriptRead:
    """Update manuscript metadata."""
    # Verify ownership
    if not service.check_ownership(manuscript_id, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    try:
        manuscript = service.update_metadata(
            manuscript_id,
            author_id,
            title=update_in.title,
            description=update_in.description,
            genre_ids=update_in.genre_ids,
            tag_names=update_in.tag_names,
        )
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    return ManuscriptRead.model_validate(manuscript)


@router.put("/{manuscript_id}/file", response_model=ManuscriptRead)
async def update_manuscript_file(
    manuscript_id: UUID,
    author_id: CurrentAuthorId,
    source_format: Annotated[SourceFormat, Form()],
    file: Annotated[UploadFile, File()],
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
) -> ManuscriptRead:
    """
    Replace the manuscript source file.

    This will reset the manuscript state to DRAFT.
    """
    # Verify ownership
    if not service.check_ownership(manuscript_id, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")

    filename = file.filename or f"manuscript.{source_format.value}"
    try:
        manuscript = await service.update_source(
            manuscript_id=manuscript_id,
            author_id=author_id,
            source_format=source_format,
            filename=filename,
            content=content,
        )
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    return ManuscriptRead.model_validate(manuscript)


@router.put("/{manuscript_id}/cover", response_model=ManuscriptRead)
async def upload_cover(
    manuscript_id: UUID,
    author_id: CurrentAuthorId,
    file: Annotated[UploadFile, File()],
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
) -> ManuscriptRead:
    """
    Upload a new cover image.

    The image file should be in one of the supported formats:
    - JPEG (.jpg, jpeg)
    - PNG (.png)
    """
    if not service.check_ownership(manuscript_id, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )
    filename = file.filename or "cover"
    try:
        updated = await service.update_cover(
            manuscript_id=manuscript_id,
            author_id=author_id,
            cover_image_filename=filename,
            cover_image_content=content,
        )
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ManuscriptRead.model_validate(updated)


@router.get("/{manuscript_id}/cover", response_class=FileResponse)
async def get_cover(
    manuscript_id: UUID,
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
) -> FileResponse:
    try:
        manuscript = service.get(manuscript_id)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    if manuscript.cover_image_key:
        storage = get_storage_backend()
        try:
            asset_path = await storage.get_url(manuscript.cover_image_key)
        except FileNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cover not found")

        media_type = get_content_type_for_format(asset_path.split(".")[-1])
        return FileResponse(asset_path, media_type=media_type)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cover not found")


@router.delete("/{manuscript_id}/cover", response_model=ManuscriptRead)
async def delete_cover(
    manuscript_id: UUID,
    author_id: CurrentAuthorId,
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
) -> ManuscriptRead:
    if not service.check_ownership(manuscript_id, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    try:
        updated = await service.remove_cover(manuscript_id)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    return ManuscriptRead.model_validate(updated)


@router.post("/{manuscript_id}/ready", response_model=ManuscriptRead)
def mark_manuscript_ready(
    manuscript_id: UUID,
    author_id: CurrentAuthorId,
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
) -> ManuscriptRead:
    """Mark a manuscript as ready for ebook generation."""
    if not service.check_ownership(manuscript_id, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    try:
        manuscript = service.mark_ready(manuscript_id)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")
    except InvalidStateTransition as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return ManuscriptRead.model_validate(manuscript)


@router.post("/{manuscript_id}/draft", response_model=ManuscriptRead)
def mark_manuscript_draft(
    manuscript_id: UUID,
    author_id: CurrentAuthorId,
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
) -> ManuscriptRead:
    """Mark manuscript as undergoing editing, and unavailable."""
    if not service.check_ownership(manuscript_id, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    try:
        manuscript = service.mark_draft(manuscript_id)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")
    except InvalidStateTransition as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return ManuscriptRead.model_validate(manuscript)


@router.post("/{manuscript_id}/archive", response_model=ManuscriptRead)
def archive_manuscript(
    manuscript_id: UUID,
    author_id: CurrentAuthorId,
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
) -> ManuscriptRead:
    """Archive a manuscript to hide it from normal listings."""
    if not service.check_ownership(manuscript_id, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    try:
        manuscript = service.archive(manuscript_id)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")
    except InvalidStateTransition as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return ManuscriptRead.model_validate(manuscript)


@router.post("/{manuscript_id}/unarchive", response_model=ManuscriptRead)
def unarchive_manuscript(
    manuscript_id: UUID,
    author_id: CurrentAuthorId,
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
) -> ManuscriptRead:
    """Restore an archived manuscript to ready state."""
    if not service.check_ownership(manuscript_id, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    try:
        manuscript = service.unarchive(manuscript_id)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")
    except InvalidStateTransition as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return ManuscriptRead.model_validate(manuscript)


@router.delete("/{manuscript_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_manuscript(
    manuscript_id: UUID,
    author_id: CurrentAuthorId,
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
) -> None:
    """
    Soft delete a manuscript and all associated ebooks and samples.

    Files are retained in storage for potential restoration.
    """
    if not service.check_ownership(manuscript_id, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    try:
        service.soft_delete(manuscript_id)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")


@router.post("/{manuscript_id}/restore", response_model=ManuscriptRead)
def restore_manuscript(
    manuscript_id: UUID,
    author_id: CurrentAuthorId,
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
) -> ManuscriptRead:
    """
    Restore a soft-deleted manuscript and all associated samples and ebooks.
    """
    # Check ownership including deleted manuscripts
    if not service.check_ownership(manuscript_id, author_id, include_deleted=True):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    try:
        service.restore(manuscript_id)
        manuscript = service.get(manuscript_id)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    return ManuscriptRead.model_validate(manuscript)

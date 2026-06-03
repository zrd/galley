"""
Manuscript management endpoints.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain import AuthorizationError, ManuscriptNotFound, SourceFormat
from app.repositories import (
    SQLAlchemyEbookRepository,
    SQLAlchemyManuscriptRepository,
    SQLAlchemySampleRepository,
    SQLAlchemyTagRepository,
)
from app.schemas import ManuscriptCreate, ManuscriptListItem, ManuscriptRead, ManuscriptUpdate
from app.security.auth import CurrentAuthorId
from app.services import EbookService, ManuscriptService, SampleService
from app.storage import generate_file_key, get_content_type_for_format, get_storage_backend, validate_image

router = APIRouter()


def get_manuscript_service(db: Annotated[Session, Depends(get_db)]) -> ManuscriptService:
    """Dependency to get a ManuscriptService with database session."""
    manuscript_repo = SQLAlchemyManuscriptRepository(db)
    sample_repo = SQLAlchemySampleRepository(db)
    ebook_repo = SQLAlchemyEbookRepository(db)
    tag_repo = SQLAlchemyTagRepository(db)
    return ManuscriptService(manuscript_repo, sample_repo, ebook_repo, tag_repo)


def get_sample_service(db: Annotated[Session, Depends(get_db)]) -> SampleService:
    """Dependency to get a SampleService with database session."""
    repo = SQLAlchemySampleRepository(db)
    ebook_repo = SQLAlchemyEbookRepository(db)
    return SampleService(repo, ebook_repo)


def get_ebook_service(db: Annotated[Session, Depends(get_db)]) -> EbookService:
    """Dependency to get an EbookService with database session."""
    repo = SQLAlchemyEbookRepository(db)
    return EbookService(repo)


@router.post("/", response_model=ManuscriptRead, status_code=status.HTTP_201_CREATED)
async def create_manuscript(
    author_id: CurrentAuthorId,
    title: Annotated[str, Form(min_length=1)],
    source_format: Annotated[SourceFormat, Form()],
    file: Annotated[UploadFile, File()],
    description: Annotated[str | None, Form()] = None,
    genre_ids: list[int] = Form(default=[]),
    tag_names: list[str] = Form(default=[]),
    service: ManuscriptService = Depends(get_manuscript_service),
    db: Session = Depends(get_db),
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
            status_code=422,
            detail=[{"loc": ["body", "title"], "msg": "title cannot be whitespace only", "type": "value_error"}],
        )

    # Read file contents
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )

    # Generate storage key and upload file
    filename = file.filename or f"manuscript.{source_format.value}"
    file_key = generate_file_key(author_id, filename, "manuscripts")
    content_type = get_content_type_for_format(source_format.value)

    storage = get_storage_backend()
    await storage.upload(file_key, content, content_type)

    # Create manuscript record
    manuscript = service.create(
        author_id=author_id,
        title=title,
        source_format=source_format,
        source_file_key=file_key,
        description=description,
        genre_ids=genre_ids,
        tag_names=tag_names,
    )
    return ManuscriptRead(
        id=manuscript.id,
        author_id=manuscript.author_id,
        title=manuscript.title,
        description=manuscript.description,
        genres=manuscript.genres,
        tags=manuscript.tags,
        cover_image_key=manuscript.cover_image_key,
        source_format=manuscript.source_format,
        state=manuscript.state,
        created_at=manuscript.created_at,
        updated_at=manuscript.updated_at,
    )


@router.get("/", response_model=list[ManuscriptListItem])
def list_manuscripts(
    author_id: CurrentAuthorId,
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    include_deleted: Annotated[bool, Query()] = False,
) -> list[ManuscriptListItem]:
    """List all manuscripts for the current author."""
    manuscripts = service.list_by_author(author_id, include_deleted=include_deleted)
    return [
        ManuscriptListItem(
            id=m.id,
            title=m.title,
            state=m.state,
            source_format=m.source_format,
            cover_image_key=m.cover_image_key,
            created_at=m.created_at,
            updated_at=m.updated_at,
            deleted_at=m.deleted_at,
        )
        for m in manuscripts
    ]


@router.get("/{manuscript_id}", response_model=ManuscriptRead)
def get_manuscript(
    manuscript_id: str,
    author_id: CurrentAuthorId,
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
) -> ManuscriptRead:
    """Get a specific manuscript by ID."""
    from uuid import UUID

    try:
        mid = UUID(manuscript_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    try:
        manuscript = service.get(mid)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    if manuscript.author_id != author_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    return ManuscriptRead(
        id=manuscript.id,
        author_id=manuscript.author_id,
        title=manuscript.title,
        description=manuscript.description,
        genres=manuscript.genres,
        tags=manuscript.tags,
        cover_image_key=manuscript.cover_image_key,
        source_format=manuscript.source_format,
        state=manuscript.state,
        created_at=manuscript.created_at,
        updated_at=manuscript.updated_at,
    )


@router.put("/{manuscript_id}", response_model=ManuscriptRead)
def update_manuscript(
    manuscript_id: str,
    update_in: ManuscriptUpdate,
    author_id: CurrentAuthorId,
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    db: Annotated[Session, Depends(get_db)],
) -> ManuscriptRead:
    """Update manuscript metadata."""
    from uuid import UUID

    try:
        mid = UUID(manuscript_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    # Verify ownership
    if not service.check_ownership(mid, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    try:
        manuscript = service.update_metadata(
            mid,
            author_id,
            title=update_in.title,
            description=update_in.description,
            genre_ids=update_in.genre_ids,
            tag_names=update_in.tag_names,
        )
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    return ManuscriptRead(
        id=manuscript.id,
        author_id=manuscript.author_id,
        title=manuscript.title,
        description=manuscript.description,
        genres=manuscript.genres,
        tags=manuscript.tags,
        cover_image_key=manuscript.cover_image_key,
        source_format=manuscript.source_format,
        state=manuscript.state,
        created_at=manuscript.created_at,
        updated_at=manuscript.updated_at,
    )


@router.put("/{manuscript_id}/file", response_model=ManuscriptRead)
async def update_manuscript_file(
    manuscript_id: str,
    author_id: CurrentAuthorId,
    source_format: Annotated[SourceFormat, Form()],
    file: Annotated[UploadFile, File()],
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    db: Annotated[Session, Depends(get_db)],
) -> ManuscriptRead:
    """
    Replace the manuscript source file.

    This will reset the manuscript state to DRAFT.
    """
    from uuid import UUID

    try:
        mid = UUID(manuscript_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    # Verify ownership
    if not service.check_ownership(mid, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    # Read and upload new file
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")

    filename = file.filename or f"manuscript.{source_format.value}"
    file_key = generate_file_key(author_id, filename, "manuscripts")
    content_type = get_content_type_for_format(source_format.value)

    storage = get_storage_backend()
    await storage.upload(file_key, content, content_type)

    # Update manuscript with new file
    try:
        manuscript = service.update_source(mid, file_key, source_format)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    return ManuscriptRead(
        id=manuscript.id,
        author_id=manuscript.author_id,
        title=manuscript.title,
        description=manuscript.description,
        genres=manuscript.genres,
        tags=manuscript.tags,
        cover_image_key=manuscript.cover_image_key,
        source_format=manuscript.source_format,
        state=manuscript.state,
        created_at=manuscript.created_at,
        updated_at=manuscript.updated_at,
    )


@router.put("/{manuscript_id}/cover", response_model=ManuscriptRead, status_code=status.HTTP_200_OK)
async def upload_cover(
    manuscript_id: UUID,
    author_id: CurrentAuthorId,
    file: Annotated[UploadFile, File()],
    service: ManuscriptService = Depends(get_manuscript_service),
    db: Session = Depends(get_db),
) -> ManuscriptRead:
    """
    Upload a new cover image.

    The image file should be in one of the supported formats:
    - JPEG (.jpg, jpeg)
    - PNG (.png)
    """
    if not service.check_ownership(manuscript_id, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    try:
        manuscript = service.get(manuscript_id)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )
    try:
        content_type = validate_image(content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    format_extension = {"image/jpeg": "jpg", "image/png": "png"}[content_type]
    if file.filename:
        extension = file.filename.split(".")[-1]
        if extension.lower() != format_extension:
            file.filename = file.filename + f".{format_extension}"

    filename = file.filename or f"cover.{format_extension}"
    file_key = generate_file_key(author_id, filename, "covers")

    storage = get_storage_backend()
    await storage.upload(file_key, content, content_type)
    existing_cover = manuscript.cover_image_key
    updated = service.update_cover(manuscript_id, file_key)
    if existing_cover:
        try:
            await storage.delete(existing_cover)
        except Exception as e:
            print(f"This is where I'd put my WARN: {e}\nlog, if I had one")

    return ManuscriptRead(
        id=updated.id,
        author_id=updated.author_id,
        title=updated.title,
        description=updated.description,
        genres=updated.genres,
        tags=updated.tags,
        cover_image_key=updated.cover_image_key,
        source_format=updated.source_format,
        state=updated.state,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.get("/{manuscript_id}/cover", response_class=FileResponse, status_code=status.HTTP_200_OK)
async def get_cover(
    manuscript_id: UUID,
    service: ManuscriptService = Depends(get_manuscript_service),
    db: Session = Depends(get_db),
) -> FileResponse:
    try:
        manuscript = service.get(manuscript_id)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    if manuscript.cover_image_key:
        storage = get_storage_backend()
        asset_path = await storage.get_url(manuscript.cover_image_key)
        media_type = get_content_type_for_format(asset_path.split(".")[-1])
        return FileResponse(asset_path, media_type=media_type)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cover not found")


@router.delete("/{manuscript_id}/cover", response_model=ManuscriptRead, status_code=status.HTTP_200_OK)
async def delete_cover(
    manuscript_id: UUID,
    author_id: CurrentAuthorId,
    service: ManuscriptService = Depends(get_manuscript_service),
    db: Session = Depends(get_db),
) -> ManuscriptRead:
    if not service.check_ownership(manuscript_id, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    try:
        manuscript = service.get(manuscript_id)
        existing_cover = manuscript.cover_image_key
        updated = service.remove_cover(manuscript_id)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    storage = get_storage_backend()
    if existing_cover:
        try:
            await storage.delete(existing_cover)
        except Exception as e:
            print(f"This is where I'd put my WARN: {e}\nlog, if I had one")

    return ManuscriptRead(
        id=updated.id,
        author_id=updated.author_id,
        title=updated.title,
        description=updated.description,
        genres=updated.genres,
        tags=updated.tags,
        cover_image_key=updated.cover_image_key,
        source_format=updated.source_format,
        state=updated.state,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.post("/{manuscript_id}/ready", response_model=ManuscriptRead)
def mark_manuscript_ready(
    manuscript_id: str,
    author_id: CurrentAuthorId,
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    db: Annotated[Session, Depends(get_db)],
) -> ManuscriptRead:
    """Mark a manuscript as ready for ebook generation."""
    from uuid import UUID

    try:
        mid = UUID(manuscript_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    if not service.check_ownership(mid, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    try:
        manuscript = service.mark_ready(mid)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ManuscriptRead(
        id=manuscript.id,
        author_id=manuscript.author_id,
        title=manuscript.title,
        description=manuscript.description,
        genres=manuscript.genres,
        tags=manuscript.tags,
        cover_image_key=manuscript.cover_image_key,
        source_format=manuscript.source_format,
        state=manuscript.state,
        created_at=manuscript.created_at,
        updated_at=manuscript.updated_at,
    )


@router.post("/{manuscript_id}/archive", response_model=ManuscriptRead)
def archive_manuscript(
    manuscript_id: str,
    author_id: CurrentAuthorId,
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    db: Annotated[Session, Depends(get_db)],
) -> ManuscriptRead:
    """Archive a manuscript to hide it from normal listings."""
    from uuid import UUID

    try:
        mid = UUID(manuscript_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    if not service.check_ownership(mid, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    try:
        manuscript = service.archive(mid)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ManuscriptRead(
        id=manuscript.id,
        author_id=manuscript.author_id,
        title=manuscript.title,
        description=manuscript.description,
        genres=manuscript.genres,
        tags=manuscript.tags,
        cover_image_key=manuscript.cover_image_key,
        source_format=manuscript.source_format,
        state=manuscript.state,
        created_at=manuscript.created_at,
        updated_at=manuscript.updated_at,
    )


@router.post("/{manuscript_id}/unarchive", response_model=ManuscriptRead)
def unarchive_manuscript(
    manuscript_id: str,
    author_id: CurrentAuthorId,
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    db: Annotated[Session, Depends(get_db)],
) -> ManuscriptRead:
    """Restore an archived manuscript to ready state."""
    from uuid import UUID

    try:
        mid = UUID(manuscript_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    if not service.check_ownership(mid, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    try:
        manuscript = service.unarchive(mid)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ManuscriptRead(
        id=manuscript.id,
        author_id=manuscript.author_id,
        title=manuscript.title,
        description=manuscript.description,
        genres=manuscript.genres,
        tags=manuscript.tags,
        cover_image_key=manuscript.cover_image_key,
        source_format=manuscript.source_format,
        state=manuscript.state,
        created_at=manuscript.created_at,
        updated_at=manuscript.updated_at,
    )


@router.delete("/{manuscript_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_manuscript(
    manuscript_id: str,
    author_id: CurrentAuthorId,
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """
    Soft delete a manuscript and all associated ebooks and samples.

    Files are retained in storage for potential restoration.
    """
    from uuid import UUID

    try:
        mid = UUID(manuscript_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    if not service.check_ownership(mid, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    try:
        service.soft_delete(mid)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")


@router.post("/{manuscript_id}/restore", response_model=ManuscriptRead)
def restore_manuscript(
    manuscript_id: str,
    author_id: CurrentAuthorId,
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
    db: Annotated[Session, Depends(get_db)],
) -> ManuscriptRead:
    """
    Restore a soft-deleted manuscript and all associated samples and ebooks.
    """
    from uuid import UUID

    try:
        mid = UUID(manuscript_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    # Check ownership including deleted manuscripts
    if not service.check_ownership(mid, author_id, include_deleted=True):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    try:
        service.restore(mid)
        manuscript = service.get(mid)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    return ManuscriptRead(
        id=manuscript.id,
        author_id=manuscript.author_id,
        title=manuscript.title,
        description=manuscript.description,
        genres=manuscript.genres,
        tags=manuscript.tags,
        cover_image_key=manuscript.cover_image_key,
        source_format=manuscript.source_format,
        state=manuscript.state,
        created_at=manuscript.created_at,
        updated_at=manuscript.updated_at,
    )

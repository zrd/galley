"""
Manuscript management endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain import AuthorizationError, ManuscriptNotFound, SourceFormat
from app.repositories import (
    SQLAlchemyEbookRepository,
    SQLAlchemyManuscriptRepository,
    SQLAlchemySampleRepository,
)
from app.schemas import ManuscriptCreate, ManuscriptListItem, ManuscriptRead, ManuscriptUpdate
from app.security.auth import CurrentAuthorId
from app.services import EbookService, ManuscriptService, SampleService
from app.storage import generate_file_key, get_content_type_for_format, get_storage_backend

router = APIRouter()


def get_manuscript_service(db: Annotated[Session, Depends(get_db)]) -> ManuscriptService:
    """Dependency to get a ManuscriptService with database session."""
    manuscript_repo = SQLAlchemyManuscriptRepository(db)
    sample_repo = SQLAlchemySampleRepository(db)
    ebook_repo = SQLAlchemyEbookRepository(db)
    return ManuscriptService(manuscript_repo, sample_repo, ebook_repo)


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
    )
    return ManuscriptRead(
        id=manuscript.id,
        author_id=manuscript.author_id,
        title=manuscript.title,
        description=manuscript.description,
        genres=manuscript.genres,
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
            title=update_in.title,
            description=update_in.description,
            genre_ids=update_in.genre_ids,
        )
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    return ManuscriptRead(
        id=manuscript.id,
        author_id=manuscript.author_id,
        title=manuscript.title,
        description=manuscript.description,
        genres=manuscript.genres,
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
        source_format=manuscript.source_format,
        state=manuscript.state,
        created_at=manuscript.created_at,
        updated_at=manuscript.updated_at,
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
        source_format=manuscript.source_format,
        state=manuscript.state,
        created_at=manuscript.created_at,
        updated_at=manuscript.updated_at,
    )

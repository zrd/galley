"""
Manuscript management endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
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
    repo = SQLAlchemyManuscriptRepository(db)
    return ManuscriptService(repo)


def get_sample_service(db: Annotated[Session, Depends(get_db)]) -> SampleService:
    """Dependency to get a SampleService with database session."""
    repo = SQLAlchemySampleRepository(db)
    return SampleService(repo)


def get_ebook_service(db: Annotated[Session, Depends(get_db)]) -> EbookService:
    """Dependency to get an EbookService with database session."""
    repo = SQLAlchemyEbookRepository(db)
    return EbookService(repo)


@router.post("/", response_model=ManuscriptRead, status_code=status.HTTP_201_CREATED)
async def create_manuscript(
    author_id: CurrentAuthorId,
    title: Annotated[str, Form()],
    source_format: Annotated[SourceFormat, Form()],
    file: Annotated[UploadFile, File()],
    description: Annotated[str | None, Form()] = None,
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
    )
    db.commit()

    return ManuscriptRead(
        id=manuscript.id,
        author_id=manuscript.author_id,
        title=manuscript.title,
        description=manuscript.description,
        source_format=manuscript.source_format,
        state=manuscript.state,
        created_at=manuscript.created_at,
        updated_at=manuscript.updated_at,
    )


@router.get("/", response_model=list[ManuscriptListItem])
def list_manuscripts(
    author_id: CurrentAuthorId,
    service: Annotated[ManuscriptService, Depends(get_manuscript_service)],
) -> list[ManuscriptListItem]:
    """List all manuscripts for the current author."""
    manuscripts = service.list_by_author(author_id)
    return [
        ManuscriptListItem(
            id=m.id,
            title=m.title,
            state=m.state,
            source_format=m.source_format,
            created_at=m.created_at,
            updated_at=m.updated_at,
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
        )
        db.commit()
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    return ManuscriptRead(
        id=manuscript.id,
        author_id=manuscript.author_id,
        title=manuscript.title,
        description=manuscript.description,
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
        db.commit()
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    return ManuscriptRead(
        id=manuscript.id,
        author_id=manuscript.author_id,
        title=manuscript.title,
        description=manuscript.description,
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
        db.commit()
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ManuscriptRead(
        id=manuscript.id,
        author_id=manuscript.author_id,
        title=manuscript.title,
        description=manuscript.description,
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
    ebook_service: Annotated[EbookService, Depends(get_ebook_service)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """
    Delete a manuscript and all associated ebooks and samples.

    This will also delete the source file from storage.
    """
    from uuid import UUID

    try:
        mid = UUID(manuscript_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    if not service.check_ownership(mid, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    try:
        manuscript = service.get(mid)
    except ManuscriptNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manuscript not found")

    # Delete source file from storage
    storage = get_storage_backend()
    try:
        await storage.delete(manuscript.source_file_key)
    except FileNotFoundError:
        pass  # File already deleted

    # Delete associated ebooks from storage
    ebooks = ebook_service.list_by_manuscript(mid)
    for ebook in ebooks:
        try:
            await storage.delete(ebook.file_key)
        except FileNotFoundError:
            pass

    # Delete manuscript (cascades to samples and ebooks in DB)
    service.delete(mid)
    db.commit()

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain import ManuscriptState, SourceFormat


class ManuscriptCreate(BaseModel):
    title: str
    description: str | None = None
    source_format: SourceFormat


class ManuscriptUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class ManuscriptRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    author_id: UUID
    title: str
    description: str | None
    source_format: SourceFormat
    state: ManuscriptState
    created_at: datetime
    updated_at: datetime


class ManuscriptListItem(BaseModel):
    """Lighter response model for list endpoints."""

    model_config = {"from_attributes": True}

    id: UUID
    title: str
    state: ManuscriptState
    source_format: SourceFormat
    created_at: datetime
    updated_at: datetime
